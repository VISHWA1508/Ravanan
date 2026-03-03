const express = require('express');
const { spawn, execSync } = require('child_process');
const { MongoClient } = require('mongodb');
const cors = require('cors');
const path = require('path');

// ── Kill any process already using PORT before starting ──
function killPort(port) {
  try {
    if (process.platform === 'win32') {
      const out = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf8' });
      const pids = new Set();
      out.trim().split('\n').forEach(line => {
        const parts = line.trim().split(/\s+/);
        if (line.includes('LISTENING') && parts.length >= 5) {
          pids.add(parts[parts.length - 1]);
        }
      });
      pids.forEach(pid => {
        if (pid && pid !== '0') {
          try { execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' }); } catch { }
        }
      });
    } else {
      execSync(`lsof -ti:${port} | xargs kill -9 2>/dev/null || true`, { stdio: 'ignore' });
    }
  } catch { /* port was free — nothing to kill */ }
}

const app = express();
const PORT = 3000;

const MONGO_URI = 'mongodb://localhost:27017/';
const DB_NAME = 'ravanan';

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ── Global process tracker ──
let activeProcess = null;
let activeProcessStopped = false;

// Pipeline stage definitions for progress tracking
const PIPELINE_STAGES = [
  { keyword: 'Starting optimized research pipeline', label: 'Initializing Pipeline', progress: 2 },
  { keyword: 'System Status', label: 'Checking System Resources', progress: 5 },
  { keyword: 'Starting optimized search pipeline', label: 'Starting Search Pipeline', progress: 8 },
  { keyword: 'Running top-down search', label: 'Running Top-Down Search', progress: 12 },
  { keyword: 'Running bottom-up search', label: 'Running Bottom-Up Search', progress: 18 },
  { keyword: 'Running CANSLIM search', label: 'Running CANSLIM Search', progress: 24 },
  { keyword: 'unique links to process', label: 'Links Discovered', progress: 28 },
  { keyword: 'Fetching financial data', label: 'Fetching Financial Data', progress: 35 },
  { keyword: 'Fetching core company info', label: 'Fetching Company Info', progress: 38 },
  { keyword: 'Fetching market data', label: 'Fetching Market Data', progress: 42 },
  { keyword: 'Fetching financial statements', label: 'Fetching Financial Statements', progress: 46 },
  { keyword: 'Fetching earnings data', label: 'Fetching Earnings Data', progress: 50 },
  { keyword: 'Fetching analyst data', label: 'Fetching Analyst Data', progress: 54 },
  { keyword: 'Financial data with comprehensive', label: 'Financial Data Saved', progress: 58 },
  { keyword: 'Pausing briefly before summarization', label: 'Preparing AI Suggestions', progress: 61 },
  { keyword: 'Starting sequential summarization', label: 'Generating AI Suggestions', progress: 64 },
  { keyword: 'Running top-down summarization', label: 'Top-Down AI Suggestion', progress: 70 },
  { keyword: 'Running bottom-up summarization', label: 'Bottom-Up AI Suggestion', progress: 78 },
  { keyword: 'Running CANSLIM summarization', label: 'CANSLIM AI Suggestion', progress: 86 },
  { keyword: 'All summarizations completed', label: 'AI Suggestions Complete', progress: 92 },
  { keyword: 'Top-Down Summary: Generated', label: 'Top-Down Suggestion Ready', progress: 94 },
  { keyword: 'Bottom-Up Summary: Generated', label: 'Bottom-Up Suggestion Ready', progress: 96 },
  { keyword: 'CANSLIM Summary: Generated', label: 'CANSLIM Suggestion Ready', progress: 98 },
  { keyword: 'Optimized pipeline completed', label: 'Pipeline Complete!', progress: 100 },
];

// ── SSE endpoint ──
app.get('/api/run', (req, res) => {
  const { company, ticker } = req.query;
  if (!company || !ticker) return res.status(400).json({ error: 'Company and ticker are required' });

  // Kill any previously running process
  if (activeProcess) {
    try { activeProcess.kill('SIGTERM'); } catch (_) { }
    activeProcess = null;
  }
  activeProcessStopped = false;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();

  const sendEvent = (type, data) => {
    try { res.write(`data: ${JSON.stringify({ type, ...data })}\n\n`); } catch (_) { }
  };

  sendEvent('start', { message: `Starting analysis for ${company} (${ticker})...`, progress: 0, label: 'Initializing...' });

  const projectRoot = path.resolve(__dirname, '..');

  // ── Prefer the project venv Python so all packages are pre-installed ──
  const venvPython = process.platform === 'win32'
    ? path.join(projectRoot, 'venv', 'Scripts', 'python.exe')
    : path.join(projectRoot, 'venv', 'bin', 'python3');
  const systemPython = process.platform === 'win32' ? 'python' : 'python3';
  const fs = require('fs');
  const pythonExe = fs.existsSync(venvPython) ? venvPython : systemPython;
  console.log(`[runner] Using Python: ${pythonExe}`);

  // Add venv Scripts dir to PATH so child sub-processes also use venv packages
  const venvScripts = path.join(projectRoot, 'venv', process.platform === 'win32' ? 'Scripts' : 'bin');
  const env = {
    ...process.env,
    PATH: `${venvScripts}${path.delimiter}${process.env.PATH}`,
    VIRTUAL_ENV: path.join(projectRoot, 'venv'),
    RAVANAN_COMPANY: company,
    RAVANAN_TICKER: ticker,
    // Force UTF-8 so emoji in log statements don't crash on Windows (cp1252 default)
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1'
  };

  const child = spawn(pythonExe, ['main.py'], { cwd: projectRoot, env });
  activeProcess = child;

  let currentProgress = 0;
  let buffer = '';

  const processLine = (line) => {
    if (!line.trim()) return;
    sendEvent('log', { message: line });
    for (const stage of PIPELINE_STAGES) {
      if (line.includes(stage.keyword) && stage.progress > currentProgress) {
        currentProgress = stage.progress;
        sendEvent('progress', { progress: currentProgress, label: stage.label });
        break;
      }
    }
  };

  child.stdout.on('data', (data) => {
    buffer += data.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop();
    lines.forEach(processLine);
  });

  child.stderr.on('data', (data) => {
    data.toString().split('\n').forEach(line => {
      if (!line.trim()) return;
      sendEvent('log', { message: line });
      for (const stage of PIPELINE_STAGES) {
        if (line.includes(stage.keyword) && stage.progress > currentProgress) {
          currentProgress = stage.progress;
          sendEvent('progress', { progress: currentProgress, label: stage.label });
          break;
        }
      }
    });
  });

  child.on('close', (code) => {
    if (buffer.trim()) processLine(buffer);
    activeProcess = null;

    if (activeProcessStopped) {
      sendEvent('stopped', { message: 'Pipeline was stopped by user.' });
    } else if (code === 0) {
      sendEvent('progress', { progress: 100, label: 'Pipeline Complete!' });
      sendEvent('done', { success: true, message: 'Analysis completed successfully!' });
    } else {
      sendEvent('done', { success: false, message: `Pipeline exited with code ${code}` });
    }
    res.end();
  });

  child.on('error', (err) => {
    activeProcess = null;
    sendEvent('error', { message: `Failed to start pipeline: ${err.message}` });
    res.end();
  });

  req.on('close', () => {
    if (activeProcess && !activeProcessStopped) {
      try { activeProcess.kill(); } catch (_) { }
      activeProcess = null;
    }
  });
});

// ── STOP endpoint ──
app.post('/api/stop', (req, res) => {
  if (!activeProcess) {
    return res.json({ success: false, message: 'No pipeline is currently running.' });
  }
  activeProcessStopped = true;
  try {
    if (process.platform === 'win32') {
      // taskkill /F /T kills the process tree (Python + all its children)
      spawn('taskkill', ['/pid', String(activeProcess.pid), '/f', '/t']);
    } else {
      activeProcess.kill('SIGTERM');
    }
    activeProcess = null;
    return res.json({ success: true, message: 'Pipeline stopped successfully.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
});

// ── Cache Check (last 7 days) ──
app.get('/api/check', async (req, res) => {
  const { ticker } = req.query;
  if (!ticker) return res.status(400).json({ error: 'Ticker required' });

  const client = new MongoClient(MONGO_URI);
  try {
    await client.connect();
    const db = client.db(DB_NAME);
    const q = ticker.toUpperCase();   // e.g. "TCS.NS"
    const qLower = ticker.toLowerCase(); // fallback

    // 7-day cutoff
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 7);

    // Query by ticker OR ticker_symbol field; fall back to company if not found
    const tickerFilter = (dateField) => ({
      $and: [
        { $or: [{ ticker: q }, { ticker: qLower }, { ticker_symbol: q }, { ticker_symbol: qLower }] },
        { [dateField]: { $gte: cutoff } }
      ]
    });

    const [topDown, bottomUp, canslim, financial] = await Promise.all([
      db.collection('top_down_summarization').findOne(tickerFilter('summarized_at'), { projection: { summarized_at: 1 } }),
      db.collection('bottom_up_summarization').findOne(tickerFilter('summarized_at'), { projection: { summarized_at: 1 } }),
      db.collection('canslim_summarization').findOne(tickerFilter('summarized_at'), { projection: { summarized_at: 1 } }),
      db.collection('financial_data').findOne(tickerFilter('fetched_at'), { projection: { fetched_at: 1 } }),
    ]);

    const dates = [
      topDown?.summarized_at,
      bottomUp?.summarized_at,
      canslim?.summarized_at,
      financial?.fetched_at,
    ].filter(Boolean).map(d => new Date(d));

    const hasCache = !!(topDown || bottomUp || canslim || financial);
    const newestDate = hasCache ? new Date(Math.max(...dates)) : null;
    const oldestDate = hasCache ? new Date(Math.min(...dates)) : null;

    res.json({
      hasCache,
      newestDate,
      oldestDate,
      available: {
        top_down: !!topDown,
        bottom_up: !!bottomUp,
        canslim: !!canslim,
        financial: !!financial,
      }
    });
  } catch (err) {
    console.error('Cache check error:', err);
    res.status(500).json({ error: err.message });
  } finally {
    await client.close();
  }
});

// ── Results from MongoDB ──
app.get('/api/results', async (req, res) => {
  const { company } = req.query;
  if (!company) return res.status(400).json({ error: 'Company name required' });

  const client = new MongoClient(MONGO_URI);
  try {
    await client.connect();
    const db = client.db(DB_NAME);
    const q = company.toLowerCase();
    const [topDown, bottomUp, canslim, financial] = await Promise.all([
      db.collection('top_down_summarization').findOne({ company: q }),
      db.collection('bottom_up_summarization').findOne({ company: q }),
      db.collection('canslim_summarization').findOne({ company: q }),
      db.collection('financial_data').findOne({ company: q }),
    ]);
    res.json({ top_down: topDown, bottom_up: bottomUp, canslim, financial });
  } catch (err) {
    console.error('MongoDB error:', err);
    res.status(500).json({ error: 'Database error: ' + err.message });
  } finally {
    await client.close();
  }
});

// ── Pages ──
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));
app.get('/analyze', (req, res) => res.sendFile(path.join(__dirname, 'public', 'analyze.html')));
app.get('/loading', (req, res) => res.sendFile(path.join(__dirname, 'public', 'loading.html')));
app.get('/results', (req, res) => res.sendFile(path.join(__dirname, 'public', 'results.html')));

// ── Start: kill stale process first, then listen ──
console.log(`⏳ Checking port ${PORT}...`);
killPort(PORT);
setTimeout(() => {
  app.listen(PORT, () => {
    console.log(`\n🚀 Ravanan running at http://localhost:${PORT}`);
    console.log(`   → Home:     http://localhost:${PORT}/`);
    console.log(`   → Analyze:  http://localhost:${PORT}/analyze`);
    console.log(`   → Results:  http://localhost:${PORT}/results\n`);
  }).on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`❌ Port ${PORT} still in use. Retrying in 1s...`);
      setTimeout(() => {
        killPort(PORT);
        app.listen(PORT, () => console.log(`🚀 Ravanan running at http://localhost:${PORT} (retry)`));
      }, 1000);
    } else {
      throw err;
    }
  });
}, 300);
