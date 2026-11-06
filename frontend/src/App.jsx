import React, { useState, useEffect } from 'react';
import { 
  Shield, CheckCircle2, AlertTriangle, XCircle, Search, Upload, 
  FileText, Activity, Clock, Layers, HelpCircle, ArrowRight, 
  Eye, Filter, Download, RefreshCw, Check, X, User, ChevronRight, 
  ChevronDown, ExternalLink, Cpu, Sliders, Database, Sparkles, 
  AlertCircle, ThumbsUp, ThumbsDown, Edit3, Settings, 
  BarChart2, FileCheck, Plus, Trash2, ArrowUpRight, MessageSquare, Info
} from 'lucide-react';

// Mock Knowledge Sources
const INITIAL_SOURCES = [
  { id: 'SRC-001', name: 'FDA_Clinical_Trial_Dosage_Guide_2025.pdf', type: 'PDF', size: '2.4 MB', chunks: 142, date: '2026-09-12', status: 'Indexed', score: '99.4%', category: 'Medical' },
  { id: 'SRC-002', name: 'Q3_2026_Financial_Earnings_Report.pdf', type: 'PDF', size: '4.1 MB', chunks: 310, date: '2026-09-28', status: 'Indexed', score: '98.8%', category: 'Financial' },
  { id: 'SRC-003', name: 'Enterprise_Architecture_Security_Spec.md', type: 'MD', size: '1.2 MB', chunks: 88, date: '2026-10-01', status: 'Indexed', score: '96.2%', category: 'Technical' },
  { id: 'SRC-004', name: 'EU_AI_Act_Compliance_Handbook_2026.pdf', type: 'PDF', size: '5.8 MB', chunks: 520, date: '2026-09-15', status: 'Indexed', score: '99.1%', category: 'Legal' },
  { id: 'SRC-005', name: 'Product_API_Endpoints_Documentation.json', type: 'JSON', size: '640 KB', chunks: 45, date: '2026-10-01', status: 'Processing', score: 'Pending', category: 'Technical' },
  { id: 'SRC-006', name: 'Medical_Clinical_Guidelines_v2.docx', type: 'DOCX', size: '1.9 MB', chunks: 112, date: '2026-08-30', status: 'Queued', score: 'Pending', category: 'Medical' }
];

// Mock Verification Reports
const SAMPLE_VERIFICATIONS = [
  {
    id: 'VER-8841',
    query: 'What is the maximum daily dosage of Paxlovid for patients with moderate renal impairment?',
    text: 'For patients with moderate renal impairment (eGFR 30 to 60 mL/min), the reduced dosage of Paxlovid is 150 mg nirmatrelvir and 100 mg ritonavir twice daily for 5 days. Daily maximum total nirmatrelvir intake must not exceed 300 mg. Administration without food adjustment is acceptable.',
    score: 94,
    status: 'Supported',
    timestamp: '2026-10-01 14:22:10',
    model: 'GPT-4o (Fine-tuned)',
    claims: [
      { id: 'c1', text: 'For patients with moderate renal impairment (eGFR 30 to 60 mL/min), the reduced dosage of Paxlovid is 150 mg nirmatrelvir and 100 mg ritonavir twice daily for 5 days.', status: 'supported', score: 0.98, source: 'FDA_Clinical_Trial_Dosage_Guide_2025.pdf', snippet: 'Section 2.2: Dose reduction in moderate renal impairment (eGFR ≥30 to <60 mL/min): 150 mg nirmatrelvir and 100 mg ritonavir twice daily for 5 days.', page: 14 },
      { id: 'c2', text: 'Daily maximum total nirmatrelvir intake must not exceed 300 mg.', status: 'supported', score: 0.95, source: 'FDA_Clinical_Trial_Dosage_Guide_2025.pdf', snippet: 'Section 2.2 Table 1: Total daily nirmatrelvir dose shall be 300 mg (150 mg BID).', page: 15 },
      { id: 'c3', text: 'Administration without food adjustment is acceptable.', status: 'supported', score: 0.91, source: 'FDA_Clinical_Trial_Dosage_Guide_2025.pdf', snippet: 'Section 2.1: Paxlovid can be taken with or without food.', page: 12 }
    ]
  },
  {
    id: 'VER-8840',
    query: 'Summarize Q3 2026 revenue and YoY growth for Cloud Services division.',
    text: 'Cloud Services revenue reached $42.8 million in Q3 2026, representing a YoY growth of 34.5%. Margin increased by 4.2% driven by server efficiency upgrades.',
    score: 68,
    status: 'Uncertain',
    timestamp: '2026-10-01 12:05:44',
    model: 'Claude 3.5 Sonnet',
    claims: [
      { id: 'c4', text: 'Cloud Services revenue reached $42.8 million in Q3 2026', status: 'supported', score: 0.96, source: 'Q3_2026_Financial_Earnings_Report.pdf', snippet: 'Cloud division gross revenues closed at $42.8M for the third quarter ended Sept 30, 2026.', page: 4 },
      { id: 'c5', text: 'representing a YoY growth of 34.5%', status: 'unsupported', score: 0.22, source: 'Q3_2026_Financial_Earnings_Report.pdf', snippet: 'Year-over-year revenue expansion for Cloud Services was 28.1% compared to Q3 2025 ($33.4M).', page: 4 },
      { id: 'c6', text: 'Margin increased by 4.2% driven by server efficiency upgrades.', status: 'uncertain', score: 0.58, source: 'Q3_2026_Financial_Earnings_Report.pdf', snippet: 'Gross margins improved by 3.8 percentage points overall due to infrastructure optimizations.', page: 7 }
    ]
  },
  {
    id: 'VER-8839',
    query: 'What are the OAuth2 token expiration timeouts specified in our API spec?',
    text: 'Access tokens expire strictly after 15 minutes, whereas refresh tokens remain valid for up to 90 days. Failed authorization attempts lockout IP for 2 hours.',
    score: 42,
    status: 'Unsupported',
    timestamp: '2026-10-01 09:41:02',
    model: 'Custom LLM Pipeline',
    claims: [
      { id: 'c7', text: 'Access tokens expire strictly after 15 minutes', status: 'unsupported', score: 0.15, source: 'Enterprise_Architecture_Security_Spec.md', snippet: 'Standard access token lifecycle is 60 minutes (3600 seconds) for standard clients.', page: 22 },
      { id: 'c8', text: 'whereas refresh tokens remain valid for up to 90 days.', status: 'supported', score: 0.92, source: 'Enterprise_Architecture_Security_Spec.md', snippet: 'Refresh tokens carry a maximum lifespan of 90 calendar days subject to key rotation.', page: 23 },
      { id: 'c9', text: 'Failed authorization attempts lockout IP for 2 hours.', status: 'unsupported', score: 0.08, source: 'Enterprise_Architecture_Security_Spec.md', snippet: 'Brute-force protection triggers temporary IP ban of 15 minutes after 5 continuous failures.', page: 29 }
    ]
  }
];

// Mock Review Queue
const INITIAL_REVIEW_QUEUE = [
  {
    id: 'REV-104',
    verId: 'VER-8840',
    claimText: 'representing a YoY growth of 34.5%',
    aiAssessment: 'Unsupported (Found 28.1% in source)',
    confidence: 0.68,
    category: 'Financial',
    source: 'Q3_2026_Financial_Earnings_Report.pdf',
    evidence: 'Year-over-year revenue expansion for Cloud Services was 28.1% compared to Q3 2025 ($33.4M).',
    date: '2026-10-01 12:05'
  },
  {
    id: 'REV-105',
    verId: 'VER-8832',
    claimText: 'All medical records must be stored in encrypted S3 buckets with KMS customer-managed keys.',
    aiAssessment: 'Uncertain (Partial keyword overlap)',
    confidence: 0.54,
    category: 'Legal',
    source: 'EU_AI_Act_Compliance_Handbook_2026.pdf',
    evidence: 'Sensitive records shall be secured using AES-256 or higher encryption at rest with automated key rotation policies.',
    date: '2026-09-30 18:12'
  },
  {
    id: 'REV-106',
    verId: 'VER-8828',
    claimText: 'Pediatric dosage is capped at 10mg/kg daily.',
    aiAssessment: 'Uncertain (Missing age bracket context)',
    confidence: 0.61,
    category: 'Medical',
    source: 'FDA_Clinical_Trial_Dosage_Guide_2025.pdf',
    evidence: 'Pediatric patients (ages 6 to 12) maximum daily dosage is restricted to 10 mg/kg unless specifically directed by pediatric specialist.',
    date: '2026-09-30 15:40'
  }
];

// Mock Audit Logs
const INITIAL_AUDIT_LOGS = [
  { id: 'LOG-9921', verId: 'VER-8841', topic: 'Paxlovid Dosage Verification', score: 94, status: 'Supported', reviewer: 'Automated AI', timestamp: '2026-10-01 14:22' },
  { id: 'LOG-9920', verId: 'VER-8840', topic: 'Q3 Financial Earnings Summary', score: 68, status: 'Flagged', reviewer: 'Pending Human', timestamp: '2026-10-01 12:05' },
  { id: 'LOG-9919', verId: 'VER-8839', topic: 'OAuth2 Security Tokens', score: 42, status: 'Unsupported', reviewer: 'Automated AI', timestamp: '2026-10-01 09:41' },
  { id: 'LOG-9918', verId: 'VER-8835', topic: 'GDPR Data Retention Mandate', score: 98, status: 'Supported', reviewer: 'Sarah Jenkins (Auditor)', timestamp: '2026-09-30 22:15' },
  { id: 'LOG-9917', verId: 'VER-8831', topic: 'API Rate Limits Tier 3', score: 12, status: 'Corrected', reviewer: 'Dr. M. Vance', timestamp: '2026-09-30 19:04' },
  { id: 'LOG-9916', verId: 'VER-8829', topic: 'Clinical Study Phase II Toxicity', score: 89, status: 'Supported', reviewer: 'Dr. M. Vance', timestamp: '2026-09-30 16:30' }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sources, setSources] = useState(INITIAL_SOURCES);
  const [verifications, setVerifications] = useState(SAMPLE_VERIFICATIONS);
  const [reviewQueue, setReviewQueue] = useState(INITIAL_REVIEW_QUEUE);
  const [auditLogs, setAuditLogs] = useState(INITIAL_AUDIT_LOGS);
  
  // Selection and Modal State
  const [activeVerification, setActiveVerification] = useState(SAMPLE_VERIFICATIONS[0]);
  const [selectedClaim, setSelectedClaim] = useState(SAMPLE_VERIFICATIONS[0].claims[0]);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [activeEvidenceDoc, setActiveEvidenceDoc] = useState(null);

  // Toast Notification
  const [toast, setToast] = useState(null);

  const triggerToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 font-sans antialiased overflow-hidden">
      {/* Left Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shrink-0 select-none">
        <div className="p-5 flex items-center gap-3 border-b border-slate-800/80">
          <div className="p-2 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg tracking-wide flex items-center gap-1.5">
              TruthGuard <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 bg-teal-950 text-teal-400 border border-teal-800 rounded">PRO</span>
            </h1>
            <p className="text-xs text-slate-400">AI Fact & Evidence Engine</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <NavItem 
            icon={<Activity className="w-4 h-4" />} 
            label="Dashboard" 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
          />
          <NavItem 
            icon={<Database className="w-4 h-4" />} 
            label="Source Upload" 
            badge={sources.length}
            active={activeTab === 'sources'} 
            onClick={() => setActiveTab('sources')} 
          />
          <NavItem 
            icon={<Sparkles className="w-4 h-4" />} 
            label="Ask & Verify" 
            active={activeTab === 'verify'} 
            onClick={() => setActiveTab('verify')} 
          />
          <NavItem 
            icon={<FileCheck className="w-4 h-4" />} 
            label="Verification Results" 
            active={activeTab === 'results'} 
            onClick={() => setActiveTab('results')} 
          />
          <NavItem 
            icon={<AlertCircle className="w-4 h-4" />} 
            label="Review Queue" 
            badge={reviewQueue.length}
            badgeColor="bg-amber-500/20 text-amber-400 border border-amber-500/30"
            active={activeTab === 'review'} 
            onClick={() => setActiveTab('review')} 
          />
          <NavItem 
            icon={<Layers className="w-4 h-4" />} 
            label="Audit Log" 
            active={activeTab === 'audit'} 
            onClick={() => setActiveTab('audit')} 
          />
        </nav>

        {/* System Status Footer */}
        <div className="p-3 mx-3 mb-3 rounded-xl bg-slate-800/60 border border-slate-700/50 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-slate-200 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Engine Online
            </span>
            <span className="text-[10px] text-slate-400 font-mono">v2.4.1</span>
          </div>
          <div className="text-[11px] text-slate-400 mb-2">99.82% RAG Retrieval Precision</div>
          <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
            <div className="bg-teal-400 h-1.5 rounded-full w-[99.8%]"></div>
          </div>
        </div>

        {/* User Account */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-teal-600/30 border border-teal-500/40 text-teal-300 font-semibold flex items-center justify-center text-xs">
              JV
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">Dr. Julian Vance</p>
              <p className="text-[11px] text-slate-400 truncate">Lead Compliance Auditor</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50">
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-xs z-10">
          <div className="flex items-center gap-3 text-slate-500 text-sm">
            <span className="font-semibold text-slate-800 capitalize">{activeTab.replace('-', ' ')}</span>
            <ChevronRight className="w-4 h-4 text-slate-300" />
            <span className="text-xs text-slate-400 hidden sm:inline">TruthGuard Fact Verification & Evidence Alignment Workbench</span>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setActiveTab('verify')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium text-xs shadow-xs transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Verification</span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {activeTab === 'dashboard' && (
            <DashboardView 
              verifications={verifications} 
              sources={sources}
              reviewQueue={reviewQueue}
              setActiveTab={setActiveTab}
              setActiveVerification={setActiveVerification}
            />
          )}

          {activeTab === 'sources' && (
            <SourcesView 
              sources={sources} 
              setSources={setSources} 
              triggerToast={triggerToast} 
            />
          )}

          {activeTab === 'verify' && (
            <AskVerifyView 
              sources={sources}
              onVerifyComplete={(newResult) => {
                setVerifications([newResult, ...verifications]);
                setActiveVerification(newResult);
                setSelectedClaim(newResult.claims[0] || null);
                setActiveTab('results');
                triggerToast('Verification completed successfully!');
              }}
            />
          )}

          {activeTab === 'results' && (
            <ResultsView 
              verification={activeVerification}
              selectedClaim={selectedClaim}
              setSelectedClaim={setSelectedClaim}
              onOpenSourceModal={(docName) => {
                setActiveEvidenceDoc(docName);
                setEvidenceModalOpen(true);
              }}
              onSendToQueue={(claim) => {
                const newItem = {
                  id: `REV-${Math.floor(100 + Math.random() * 900)}`,
                  verId: activeVerification.id,
                  claimText: claim.text,
                  aiAssessment: 'Flagged manually from inspection',
                  confidence: claim.score,
                  category: 'General',
                  source: claim.source,
                  evidence: claim.snippet,
                  date: new Date().toISOString().replace('T', ' ').substring(0, 16)
                };
                setReviewQueue([newItem, ...reviewQueue]);
                triggerToast('Claim escalated to Human Review Queue', 'info');
              }}
            />
          )}

          {activeTab === 'review' && (
            <HumanReviewView 
              queue={reviewQueue} 
              setQueue={setReviewQueue}
              triggerToast={triggerToast}
            />
          )}

          {activeTab === 'audit' && (
            <AuditLogView logs={auditLogs} />
          )}
        </main>
      </div>

      {/* Evidence Modal */}
      {evidenceModalOpen && (
        <EvidenceViewerModal 
          docName={activeEvidenceDoc}
          selectedClaim={selectedClaim}
          onClose={() => setEvidenceModalOpen(false)}
        />
      )}

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-xl border border-slate-700 flex items-center gap-3 text-sm animate-bounce">
          <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0" />
          <span>{toast.msg}</span>
        </div>
      )}
    </div>
  );
}

function NavItem({ icon, label, badge, badgeColor, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
        active 
          ? 'bg-teal-600/15 text-teal-300 border border-teal-500/20 font-semibold' 
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
      }`}
    >
      <div className="flex items-center gap-2.5">
        <span className={active ? 'text-teal-400' : 'text-slate-400'}>{icon}</span>
        <span>{label}</span>
      </div>
      {badge !== undefined && (
        <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${badgeColor || 'bg-slate-800 text-slate-300'}`}>
          {badge}
        </span>
      )}
    </button>
  );
}

function DashboardView({ verifications, sources, reviewQueue, setActiveTab, setActiveVerification }) {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 p-6 rounded-2xl text-white shadow-md relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight">AI Fact-Check & Verification Command Center</h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">
              Cross-reference LLM output against enterprise knowledge vectors in real-time. Detect hallucinations, verify source provenance, and manage compliance queues.
            </p>
          </div>
          <button 
            onClick={() => setActiveTab('verify')}
            className="self-start md:self-auto px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg transition-all flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> Start Fact-Check
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Answers Checked"
          value="1,482"
          trend="+12% this week"
          icon={<FileCheck className="w-5 h-5 text-teal-600" />}
          bgColor="bg-teal-50"
        />
        <MetricCard 
          title="Accuracy Rate"
          value="84.2%"
          subtext="84.2% Supported | 11.5% Uncertain | 4.3% Unsupported"
          progress={84.2}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
          bgColor="bg-emerald-50"
        />
        <MetricCard 
          title="Active Indexed Sources"
          value={sources.filter(s => s.status === 'Indexed').length.toString()}
          subtext="24 Documents Total"
          icon={<Database className="w-5 h-5 text-blue-600" />}
          bgColor="bg-blue-50"
        />
        <MetricCard 
          title="Pending Review Queue"
          value={reviewQueue.length.toString()}
          subtext="Requires Auditor Signoff"
          icon={<AlertTriangle className="w-5 h-5 text-amber-600" />}
          bgColor="bg-amber-50"
        />
      </div>

      {/* Visual Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Verification Confidence Breakdown</h3>
              <p className="text-xs text-slate-500">Distribution of factuality scores across domain knowledge categories</p>
            </div>
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded">Last 30 Days</span>
          </div>

          <div className="space-y-4 pt-2">
            <BarMetric label="Medical & Clinical Guidelines" percentage={92} supported={88} uncertain={8} unsupported={4} />
            <BarMetric label="Financial Earnings & Audits" percentage={84} supported={84} uncertain={11} unsupported={5} />
            <BarMetric label="Legal & Regulatory Standards" percentage={90} supported={90} uncertain={7} unsupported={3} />
            <BarMetric label="Technical & API Specs" percentage={76} supported={76} uncertain={16} unsupported={8} />
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-around text-xs text-slate-500">
            <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-xs bg-emerald-500"></span> Supported</div>
            <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-xs bg-amber-400"></span> Uncertain</div>
            <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-xs bg-rose-500"></span> Unsupported</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-800 text-sm">Knowledge Base Overview</h3>
              <button onClick={() => setActiveTab('sources')} className="text-xs text-teal-600 hover:underline font-medium">Manage</button>
            </div>
            <p className="text-xs text-slate-500 mb-4">6 active indexed documents available for ground-truth verification.</p>

            <div className="space-y-3">
              {sources.slice(0, 4).map((src) => (
                <div key={src.id} className="p-2.5 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                    <span className="font-medium text-slate-700 truncate">{src.name}</span>
                  </div>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${
                    src.status === 'Indexed' ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : 'text-amber-600 bg-amber-50 border-amber-200'
                  }`}>
                    {src.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button 
            onClick={() => setActiveTab('sources')} 
            className="w-full mt-4 py-2 border border-dashed border-slate-300 hover:border-teal-500 text-slate-600 hover:text-teal-600 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
          >
            <Upload className="w-3.5 h-3.5" /> Upload Document
          </button>
        </div>
      </div>

      {/* Recent Verifications Activity */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-slate-800 text-sm">Recent Verification Activity</h3>
            <p className="text-xs text-slate-500">Live output checks against active vector knowledge bases</p>
          </div>
          <button 
            onClick={() => setActiveTab('audit')} 
            className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1"
          >
            View Full Audit Log <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="p-3.5 pl-5">ID & Query</th>
                <th className="p-3.5">Model</th>
                <th className="p-3.5">Trust Score</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5 pr-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {verifications.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 pl-5">
                    <div className="font-semibold text-slate-800">{item.id}</div>
                    <div className="text-slate-500 max-w-md truncate text-[11px]">{item.query}</div>
                  </td>
                  <td className="p-3.5 font-medium text-slate-700">{item.model}</td>
                  <td className="p-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">{item.score}%</span>
                      <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className={`h-1.5 rounded-full ${item.score > 80 ? 'bg-emerald-500' : item.score > 60 ? 'bg-amber-500' : 'bg-rose-500'}`} 
                          style={{ width: `${item.score}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3.5"><StatusBadge status={item.status} /></td>
                  <td className="p-3.5 text-slate-400 font-mono text-[11px]">{item.timestamp}</td>
                  <td className="p-3.5 pr-5 text-right">
                    <button 
                      onClick={() => {
                        setActiveVerification(item);
                        setActiveTab('results');
                      }}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-700 rounded-lg font-medium text-[11px] transition-colors"
                    >
                      Inspect Claims
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SourcesView({ sources, setSources, triggerToast }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');

  const handleSimulatedUpload = (file) => {
    setIsUploading(true);
    setUploadProgress(15);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval);
          setTimeout(() => {
            const newDoc = {
              id: `SRC-00${sources.length + 1}`,
              name: file ? file.name : 'System_Architecture_Spec.md',
              type: file ? file.name.split('.').pop().toUpperCase() : 'MD',
              size: '1.8 MB',
              chunks: 95,
              date: new Date().toISOString().split('T')[0],
              status: 'Indexed',
              score: '98.5%',
              category: 'General'
            };
            setSources([newDoc, ...sources]);
            setIsUploading(false);
            setUploadProgress(0);
            triggerToast(`Document "${newDoc.name}" uploaded and indexed successfully!`);
          }, 500);
          return 100;
        }
        return prev + 25;
      });
    }, 250);
  };

  const handleDelete = (id, name) => {
    setSources(sources.filter(s => s.id !== id));
    triggerToast(`Document "${name}" removed from knowledge base.`, 'info');
  };

  const filteredSources = sources.filter(s => s.name.toLowerCase().includes(filterQuery.toLowerCase()));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h2 className="text-lg font-bold text-slate-800">Source Upload & Knowledge Vectors</h2>
        <p className="text-xs text-slate-500">Manage grounded references used by TruthGuard for hallucination checks.</p>
      </div>

      {/* Upload Drag & Drop Area */}
      <div 
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
          dragActive ? 'border-teal-500 bg-teal-50/50' : 'border-slate-300 bg-white hover:border-slate-400'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => { e.preventDefault(); setDragActive(false); handleSimulatedUpload(e.dataTransfer.files[0]); }}
      >
        {!isUploading ? (
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mx-auto border border-teal-100">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">Drag & Drop knowledge sources here</p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF, TXT, DOCX, and Markdown (.md) files up to 50MB</p>
            </div>
            <div className="pt-2">
              <label className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs rounded-xl cursor-pointer shadow-xs inline-block">
                Browse Files
                <input 
                  type="file" 
                  accept=".pdf,.txt,.docx,.md"
                  className="hidden" 
                  onChange={(e) => handleSimulatedUpload(e.target.files[0])} 
                />
              </label>
            </div>
          </div>
        ) : (
          <div className="max-w-md mx-auto space-y-4 py-4">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-teal-600 animate-spin" />
                Processing and generating embeddings...
              </span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div className="bg-teal-500 h-2 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
            </div>
          </div>
        )}
      </div>

      {/* Indexed Sources Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input 
              type="text" 
              placeholder="Search indexed sources..." 
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs border border-slate-200 rounded-xl focus:outline-none focus:border-teal-500"
            />
          </div>
          <div className="text-xs text-slate-500 font-medium">
            Showing {filteredSources.length} of {sources.length} Documents
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="p-3.5 pl-5">Document Name</th>
                <th className="p-3.5">Category</th>
                <th className="p-3.5">Chunks</th>
                <th className="p-3.5">Size</th>
                <th className="p-3.5">Date Added</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 pr-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredSources.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 pl-5 font-semibold text-slate-800 flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-teal-600 shrink-0" />
                    <span>{doc.name}</span>
                  </td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md text-[11px] font-medium">
                      {doc.category}
                    </span>
                  </td>
                  <td className="p-3.5 font-mono text-slate-700">{doc.chunks}</td>
                  <td className="p-3.5 text-slate-400 font-mono text-[11px]">{doc.size}</td>
                  <td className="p-3.5 text-slate-400 font-mono text-[11px]">{doc.date}</td>
                  <td className="p-3.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      doc.status === 'Indexed' 
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                        : doc.status === 'Processing'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="p-3.5 pr-5 text-right flex items-center justify-end gap-1">
                    <button 
                      onClick={() => triggerToast(`Re-indexing ${doc.name}...`)}
                      className="p-1.5 text-slate-400 hover:text-teal-600 rounded-lg hover:bg-slate-100"
                      title="Re-index document"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    <button 
                      onClick={() => handleDelete(doc.id, doc.name)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100"
                      title="Delete document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function AskVerifyView({ sources, onVerifyComplete }) {
  const [inputText, setInputText] = useState('');
  const [promptText, setPromptText] = useState('');
  const [selectedModel, setSelectedModel] = useState('GPT-4o (Fine-tuned)');
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { title: 'Retrieve Context', desc: 'Fetching semantic vector matches from indexed sources...' },
    { title: 'Trace Evidence', desc: 'Aligning sentence claims with source document passages...' },
    { title: 'Evaluate Logic', desc: 'Checking for semantic discrepancies and hallucinations...' },
    { title: 'Verify Claims', desc: 'Computing factuality confidence scores and generating highlights...' }
  ];

  const handleStartVerification = () => {
    if (!inputText.trim()) return;
    setIsProcessing(true);
    setCurrentStep(0);

    let stepCounter = 0;
    const interval = setInterval(() => {
      stepCounter++;
      if (stepCounter < steps.length) {
        setCurrentStep(stepCounter);
      } else {
        clearInterval(interval);
        setTimeout(() => {
          setIsProcessing(false);

          const mockResult = {
            id: `VER-${Math.floor(8000 + Math.random() * 1000)}`,
            query: promptText.trim() || 'Custom Prompt Fact-Check Verification',
            text: inputText,
            score: Math.floor(75 + Math.random() * 20),
            status: 'Supported',
            timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
            model: selectedModel,
            claims: inputText.split('. ').filter(Boolean).map((sentence, idx) => ({
              id: `c-gen-${idx}`,
              text: sentence.endsWith('.') ? sentence : `${sentence}.`,
              status: idx % 3 === 0 ? 'supported' : idx % 3 === 1 ? 'uncertain' : 'supported',
              score: (0.75 + (idx * 0.05)) % 1,
              source: sources[idx % sources.length]?.name || 'System_Architecture_Spec.md',
              snippet: 'Extracted source excerpt matching sentence context from knowledge base vector store.',
              page: Math.floor(1 + Math.random() * 15)
            }))
          };

          onVerifyComplete(mockResult);
        }, 500);
      }
    }, 700);
  };

  const loadSample = (type) => {
    if (type === 'earnings') {
      setPromptText('Summarize Q3 2026 revenue and YoY growth for Cloud Services division.');
      setInputText('Cloud Services revenue reached $42.8 million in Q3 2026, representing a YoY growth of 34.5%. Margin increased by 4.2% driven by server efficiency upgrades.');
    } else if (type === 'clinical') {
      setPromptText('What is the maximum dosage of Paxlovid for moderate renal impairment?');
      setInputText('For patients with moderate renal impairment (eGFR 30 to 60 mL/min), the reduced dosage of Paxlovid is 150 mg nirmatrelvir and 100 mg ritonavir twice daily for 5 days. Daily maximum total intake must not exceed 300 mg.');
    } else if (type === 'tech') {
      setPromptText('What are the OAuth2 security token expiration rules?');
      setInputText('Access tokens expire strictly after 15 minutes, whereas refresh tokens remain valid for up to 90 days. Failed authorization attempts lockout IP for 2 hours.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-bold text-slate-800">Ask & Verify Answer</h2>
        <p className="text-xs text-slate-500">Input an AI-generated answer and optional prompt to verify factuality against grounded sources.</p>
      </div>

      {/* Preset Example Prompts */}
      <div className="flex items-center gap-2 text-xs flex-wrap">
        <span className="text-slate-400 font-medium">Presets:</span>
        <button onClick={() => loadSample('earnings')} className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">
          Verify Earnings Claim
        </button>
        <button onClick={() => loadSample('clinical')} className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">
          Check Clinical Dosage
        </button>
        <button onClick={() => loadSample('tech')} className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">
          Verify System API Spec
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4">
        {/* Model and Settings */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <span className="text-xs font-bold text-slate-700">Verification Workspace</span>
          <div className="flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1 bg-slate-50 font-medium text-slate-700 focus:outline-none"
            >
              <option>GPT-4o (Fine-tuned)</option>
              <option>Claude 3.5 Sonnet</option>
              <option>Custom LLM Pipeline</option>
            </select>
          </div>
        </div>

        {/* Inputs */}
        <div className="space-y-3">
          <div>
            <label className="text-[11px] font-semibold text-slate-600 block mb-1">User Question / Prompt (Optional)</label>
            <input 
              type="text"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="e.g. What is the maximum daily dosage of Paxlovid?"
              className="w-full p-2.5 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-teal-500"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-600 block mb-1">AI-Generated Answer to Check</label>
            <textarea
              rows={5}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste the generated response or paragraph here..."
              className="w-full p-3 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-teal-500 font-mono resize-none"
            />
          </div>
        </div>

        {/* Trigger Button */}
        <div className="flex items-center justify-end pt-2">
          <button
            onClick={handleStartVerification}
            disabled={!inputText.trim() || isProcessing}
            className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${
              !inputText.trim() || isProcessing
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-teal-600 hover:bg-teal-700 text-white'
            }`}
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Verifying...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4" /> Verify Claims
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Tracker Pipeline Steps */}
      {isProcessing && (
        <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xl space-y-5 border border-slate-800">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-teal-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 animate-pulse" /> Live Verification Pipeline
            </h3>
            <span className="text-xs font-mono text-slate-400">Step {currentStep + 1} of 4</span>
          </div>

          <div className="space-y-4">
            {steps.map((step, idx) => {
              const isDone = idx < currentStep;
              const isCurrent = idx === currentStep;

              return (
                <div key={idx} className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                    isDone ? 'bg-teal-500 text-slate-950' : isCurrent ? 'bg-amber-400 text-slate-950 animate-bounce' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {isDone ? <Check className="w-3.5 h-3.5" /> : idx + 1}
                  </div>
                  <div>
                    <p className={`text-xs font-semibold ${isCurrent ? 'text-white' : isDone ? 'text-slate-300' : 'text-slate-500'}`}>
                      {step.title}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{step.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function ResultsView({ verification, selectedClaim, setSelectedClaim, onOpenSourceModal, onSendToQueue }) {
  if (!verification) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Details Card */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-slate-400">{verification.id}</span>
            <StatusBadge status={verification.status} />
          </div>
          <h2 className="text-base font-bold text-slate-800 mt-1">{verification.query}</h2>
          <p className="text-xs text-slate-400 mt-0.5">Checked with {verification.model} at {verification.timestamp}</p>
        </div>

        <div className="flex items-center gap-4 bg-slate-50 px-4 py-3 rounded-xl border border-slate-100 shrink-0">
          <div className="text-right">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Factuality Score</div>
            <div className={`text-2xl font-black ${verification.score >= 80 ? 'text-emerald-600' : verification.score >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
              {verification.score}%
            </div>
          </div>
          <Shield className={`w-8 h-8 ${verification.score >= 80 ? 'text-emerald-500' : verification.score >= 60 ? 'text-amber-500' : 'text-rose-500'}`} />
        </div>
      </div>

      {/* Claim Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-800 text-sm">Color-Coded Claim Highlight</h3>
            <span className="text-[11px] text-slate-400">Click a sentence to inspect source match</span>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl leading-relaxed text-sm space-y-2">
            {verification.claims.map((claim) => {
              const isSelected = selectedClaim?.id === claim.id;
              
              let bgStyle = "bg-emerald-100/80 border-b-2 border-emerald-500 text-slate-900";
              if (claim.status === 'uncertain') {
                bgStyle = "bg-amber-100/80 border-b-2 border-amber-500 text-slate-900";
              } else if (claim.status === 'unsupported') {
                bgStyle = "bg-rose-100/80 border-b-2 border-rose-500 text-slate-900";
              }

              return (
                <span 
                  key={claim.id}
                  onClick={() => setSelectedClaim(claim)}
                  className={`inline cursor-pointer transition-all px-1 py-0.5 rounded mx-0.5 ${bgStyle} ${
                    isSelected ? 'ring-2 ring-slate-900 shadow-xs font-medium' : 'hover:opacity-80'
                  }`}
                >
                  {claim.text}{' '}
                </span>
              );
            })}
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-emerald-200 border border-emerald-500 rounded-xs"></span> Supported</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-amber-200 border border-amber-500 rounded-xs"></span> Uncertain</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-rose-200 border border-rose-500 rounded-xs"></span> Unsupported</span>
          </div>
        </div>

        {/* Evidence Drawer Details */}
        <div className="lg:col-span-5 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-800 text-sm">Evidence Drawer</h3>
            {selectedClaim && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                selectedClaim.status === 'supported' ? 'bg-emerald-100 text-emerald-800' : selectedClaim.status === 'uncertain' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
              }`}>
                {selectedClaim.status}
              </span>
            )}
          </div>

          {selectedClaim ? (
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Target Claim Sentence</label>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 font-medium">
                  "{selectedClaim.text}"
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Matched Evidence Excerpt</label>
                  <span className="text-[10px] font-mono text-teal-600 font-bold">{(selectedClaim.score * 100).toFixed(0)}% Match</span>
                </div>
                <div className="p-3 bg-teal-50/50 border border-teal-200/80 rounded-xl text-xs text-slate-700 italic">
                  "{selectedClaim.snippet}"
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl text-xs space-y-1.5">
                <div className="flex justify-between text-slate-600">
                  <span className="text-slate-400">Source:</span>
                  <span className="font-semibold text-slate-800 truncate max-w-[200px]">{selectedClaim.source}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span className="text-slate-400">Reference:</span>
                  <span className="font-semibold text-slate-800">Page {selectedClaim.page}</span>
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <button
                  onClick={() => onOpenSourceModal(selectedClaim.source)}
                  className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  <ExternalLink className="w-3.5 h-3.5" /> View Source Document Context
                </button>

                <button
                  onClick={() => onSendToQueue(selectedClaim)}
                  className="w-full py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <AlertCircle className="w-3.5 h-3.5" /> Flag & Send to Review Queue
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-slate-400 text-xs">
              Select a sentence claim on the left to inspect evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EvidenceViewerModal({ docName, selectedClaim, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
          <div className="flex items-center gap-2.5">
            <FileText className="w-5 h-5 text-teal-400" />
            <div>
              <h3 className="font-bold text-sm">{docName || 'Source Context Viewer'}</h3>
              <p className="text-[11px] text-slate-400">Matched Passage Grounding</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 p-6 overflow-y-auto font-serif text-slate-800 text-sm leading-relaxed bg-white">
          <div className="max-w-2xl mx-auto space-y-4">
            <h2 className="text-xl font-bold font-sans text-slate-900 border-b pb-2">Grounding Document Passage Context</h2>
            <p className="text-slate-600">
              The following section contains verified knowledge base documentation indexed into the vector store for truthfulness verification.
            </p>

            <div className="p-4 bg-teal-50 border-l-4 border-teal-500 my-4 text-slate-900 font-sans text-xs rounded-r-xl shadow-xs">
              <span className="font-bold text-teal-900 block mb-1 font-sans text-[10px] uppercase tracking-wider">Matched Excerpt (Page {selectedClaim?.page || 14})</span>
              {selectedClaim?.snippet || "Section 2.2: Dose reduction in moderate renal impairment (eGFR ≥30 to <60 mL/min): 150 mg nirmatrelvir and 100 mg ritonavir twice daily for 5 days."}
            </div>

            <p className="text-slate-600">
              Ensure compliance with standard clinical protocol and guidelines before overriding flagged system outputs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function HumanReviewView({ queue, setQueue, triggerToast }) {
  const [reviewNote, setReviewNote] = useState('');
  const [activeReviewItem, setActiveReviewItem] = useState(queue[0] || null);

  const handleDecision = (decision) => {
    if (!activeReviewItem) return;

    setQueue(queue.filter(item => item.id !== activeReviewItem.id));
    triggerToast(`Claim ${activeReviewItem.id} marked as ${decision}. Audit log updated.`);
    setReviewNote('');
    setActiveReviewItem(queue[1] || null);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h2 className="text-lg font-bold text-slate-800">Human Review Queue</h2>
        <p className="text-xs text-slate-500">Review flagged or uncertain AI claims awaiting auditor sign-off.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Pending Items ({queue.length})
          </div>

          {queue.map((item) => (
            <div 
              key={item.id}
              onClick={() => setActiveReviewItem(item)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                activeReviewItem?.id === item.id 
                  ? 'bg-white border-teal-500 shadow-md ring-1 ring-teal-500' 
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-slate-400">{item.id}</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                  {item.category}
                </span>
              </div>
              <p className="text-xs font-semibold text-slate-800 line-clamp-2">"{item.claimText}"</p>
              <p className="text-[11px] text-slate-400 mt-2">{item.date}</p>
            </div>
          ))}

          {queue.length === 0 && (
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 text-xs text-slate-400">
              No items awaiting review.
            </div>
          )}
        </div>

        <div className="lg:col-span-7 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-5">
          {activeReviewItem ? (
            <>
              <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm">Reviewing Claim {activeReviewItem.id}</h3>
                  <p className="text-xs text-slate-400">Verification ID: {activeReviewItem.verId}</p>
                </div>
                <span className="text-xs font-semibold text-slate-500">
                  Score: <span className="text-slate-800 font-bold">{(activeReviewItem.confidence * 100).toFixed(0)}%</span>
                </span>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Target Claim</label>
                  <div className="p-3 bg-amber-50/50 border border-amber-200 rounded-xl text-xs font-medium text-slate-800">
                    "{activeReviewItem.claimText}"
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Source Passage Snippet</label>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs italic text-slate-700">
                    "{activeReviewItem.evidence}"
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1 font-mono">Source: {activeReviewItem.source}</div>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Auditor Note</label>
                <textarea
                  rows={3}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="Enter reasoning or corrections..."
                  className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3 pt-2">
                <button
                  onClick={() => handleDecision('Approved')}
                  className="py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  <ThumbsUp className="w-3.5 h-3.5" /> Approve
                </button>
                <button
                  onClick={() => handleDecision('Rejected')}
                  className="py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  <ThumbsDown className="w-3.5 h-3.5" /> Reject
                </button>
                <button
                  onClick={() => handleDecision('Corrected')}
                  className="py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  <Edit3 className="w-3.5 h-3.5" /> Correct
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-slate-400 text-xs">
              Select an item on the left to perform auditor review.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AuditLogView({ logs }) {
  const [statusFilter, setStatusFilter] = useState('All');

  const filteredLogs = logs.filter(log => statusFilter === 'All' || log.status === statusFilter);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Audit Log</h2>
          <p className="text-xs text-slate-500">History of AI checks, status decisions, and auditor reviews.</p>
        </div>

        <button className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs">
          <Download className="w-3.5 h-3.5" /> Export Log (CSV)
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center gap-3 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-600">Filter Status:</span>
          {['All', 'Supported', 'Flagged', 'Corrected', 'Unsupported'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                statusFilter === st ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="p-3.5 pl-5">Audit ID</th>
                <th className="p-3.5">Topic</th>
                <th className="p-3.5">Score</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Verified By</th>
                <th className="p-3.5 pr-5">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 pl-5 font-mono font-semibold text-slate-800">{log.id}</td>
                  <td className="p-3.5 font-medium text-slate-800">{log.topic}</td>
                  <td className="p-3.5 font-bold">{log.score}%</td>
                  <td className="p-3.5"><StatusBadge status={log.status} /></td>
                  <td className="p-3.5 font-medium text-slate-700">{log.reviewer}</td>
                  <td className="p-3.5 pr-5 text-slate-400 font-mono text-[11px]">{log.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, trend, subtext, progress, icon, bgColor }) {
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500">{title}</span>
        <div className={`p-2 rounded-xl ${bgColor}`}>{icon}</div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-black text-slate-900">{value}</div>
        {trend && <div className="text-[11px] font-semibold text-emerald-600 mt-0.5">{trend}</div>}
        {subtext && <div className="text-[11px] text-slate-400 mt-0.5">{subtext}</div>}
      </div>
      {progress !== undefined && (
        <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
          <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${progress}%` }}></div>
        </div>
      )}
    </div>
  );
}

function BarMetric({ label, percentage, supported, uncertain, unsupported }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs font-semibold text-slate-700">
        <span>{label}</span>
        <span className="font-mono">{percentage}% Grounded</span>
      </div>
      <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden flex">
        <div style={{ width: `${supported}%` }} className="bg-emerald-500 h-full"></div>
        <div style={{ width: `${uncertain}%` }} className="bg-amber-400 h-full"></div>
        <div style={{ width: `${unsupported}%` }} className="bg-rose-500 h-full"></div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  let style = "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (status === 'Uncertain' || status === 'Flagged') {
    style = "bg-amber-50 text-amber-700 border-amber-200";
  } else if (status === 'Unsupported') {
    style = "bg-rose-50 text-rose-700 border-rose-200";
  } else if (status === 'Corrected') {
    style = "bg-blue-50 text-blue-700 border-blue-200";
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${style}`}>
      {status}
    </span>
  );
}