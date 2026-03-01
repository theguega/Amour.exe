import {
    Chart as ChartJS,
    Filler,
    Legend,
    LineElement,
    PointElement,
    RadialLinearScale,
    Tooltip,
} from 'chart.js';
import { useEffect, useState, useRef } from 'react';
import { Radar } from 'react-chartjs-2';
import './index.css';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const STAGES = ['Strangers', 'Curious', 'Flirty', 'Bonded', 'In_love'];

function App() {
  const sessionStartTime = useRef(new Date().getTime());

  const [metrics, setMetrics] = useState({
    handoffs: { girl: 0, guy: 0 },
    duration: 0,
    wordCount: { girl: 0, guy: 0 },
    emotions: {
      girl: { joy: 0, curiosity: 0, nervousness: 0 },
      guy: { joy: 0, curiosity: 0, nervousness: 0 },
    },
    stage: 'Strangers',
    girlInterest: 0,
    guyConfidence: 1,
    momentum: 0,
    toolUsage: {
      memory: 0,
      seduction: 0,
      web_search: 0
    },
    agentHandoffs: {}
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWeaveData = async () => {
      try {
        const entity = import.meta.env.VITE_WANDB_ENTITY;
        const project = import.meta.env.VITE_WANDB_PROJECT;
        const apiKey = import.meta.env.VITE_WANDB_API_KEY;

        if (!entity || !project || !apiKey) {
          console.error('Missing W&B configuration in .env');
          return;
        }

        const response = await fetch('/weave-api/calls/stream_query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Basic ${btoa(`api:${apiKey}`)}`,
          },
          body: JSON.stringify({
            project_id: `${entity}/${project}`,
            filter: {
              trace_roots_only: true
            },
            limit: 100, // Increased limit to ensure we catch all new traces from both computers
            sort_by: [
              { field: 'started_at', direction: 'desc' }
            ]
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch traces: ${response.statusText}`);
        }

        const text = await response.text();
        const lines = text.trim().split('\n');
        const traces = lines
          .map(line => {
            try {
              return JSON.parse(line);
            } catch (e) {
              return null;
            }
          })
          .filter(t => t !== null);

        const logTraces = traces.filter(t => {
          const isLog = t.op_name && t.op_name.includes('log_to_weave');
          const startedAt = new Date(t.started_at).getTime();
          return isLog && startedAt >= sessionStartTime.current;
        });

        if (logTraces.length === 0) {
          setLoading(false);
          return;
        }

        // Aggregate uniquely using trace IDs to prevent double counting 
        // across polls or multiple logging computers.
        const aggregated = logTraces.reduce((acc, trace) => {
          if (acc.seenTraceIds.has(trace.id)) return acc;
          acc.seenTraceIds.add(trace.id);

          const input = trace.inputs?.result || {};
          const output = trace.output || {};
          const agentType = input.agent_type || output.agent_type;

          const words = output.general_stats?.words_spoken_ai || 0;
          const duration = output.general_stats?.duration || 0;

          acc.totalDuration += duration;

          if (input.tool_calls && Array.isArray(input.tool_calls)) {
            input.tool_calls.forEach(tc => {
              if (tc.called && acc.toolUsage[tc.tool] !== undefined) {
                acc.toolUsage[tc.tool] += 1;
              }
            });
          }

          if (output.agent_handoffs?.frequency) {
            Object.entries(output.agent_handoffs.frequency).forEach(([agent, count]) => {
              acc.agentHandoffs[agent] = (acc.agentHandoffs[agent] || 0) + count;
            });
          }

          if (agentType === 'girl') {
            acc.handoffs.girl += 1;
            acc.wordCount.girl += words;
            if (!acc.emotionsSet.girl) {
              acc.emotions.girl = {
                joy: output.emotion_metrics?.spider_web?.joy || 0,
                curiosity: output.emotion_metrics?.spider_web?.curiosity || 0,
                nervousness: output.emotion_metrics?.spider_web?.nervousness || 0,
              };
              acc.emotionsSet.girl = true;
            }
          } else if (agentType === 'man' || agentType === 'guy') {
            acc.handoffs.guy += 1;
            acc.wordCount.guy += words;
            if (!acc.emotionsSet.guy) {
              acc.emotions.guy = {
                joy: output.emotion_metrics?.spider_web?.joy || 0,
                curiosity: output.emotion_metrics?.spider_web?.curiosity || 0,
                nervousness: output.emotion_metrics?.spider_web?.nervousness || 0,
              };
              acc.emotionsSet.guy = true;
            }
          }

          const rel = input.relationship || output.relationship_metrics;
          if (rel) {
            const rawStage = rel.stage || 'strangers';
            acc.stage = rawStage.charAt(0).toUpperCase() + rawStage.slice(1);
            acc.momentum = Number(rel.momentum) || 0;
            const score = Number(rel.compatibility_score);
            if (agentType === 'girl' && !acc.relationshipSet.girl) {
              acc.girlInterest = isNaN(score) ? 0 : score;
              acc.relationshipSet.girl = true;
            } else if ((agentType === 'man' || agentType === 'guy') && !acc.relationshipSet.guy) {
              acc.guyConfidence = isNaN(score) ? 1 : score;
              acc.relationshipSet.guy = true;
            }
          }

          return acc;
        }, {
          handoffs: { girl: 0, guy: 0 },
          duration: 0,
          totalDuration: 0,
          wordCount: { girl: 0, guy: 0 },
          emotions: {
            girl: { joy: 0, curiosity: 0, nervousness: 0 },
            guy: { joy: 0, curiosity: 0, nervousness: 0 },
          },
          stage: 'Strangers',
          girlInterest: 0,
          guyConfidence: 1,
          momentum: 0,
          toolUsage: { memory: 0, seduction: 0, web_search: 0 },
          agentHandoffs: {},
          emotionsSet: { girl: false, guy: false },
          relationshipSet: { girl: false, guy: false },
          seenTraceIds: new Set()
        });

        setMetrics({
          handoffs: aggregated.handoffs,
          duration: aggregated.totalDuration,
          wordCount: aggregated.wordCount,
          emotions: aggregated.emotions,
          stage: aggregated.stage,
          girlInterest: aggregated.girlInterest,
          guyConfidence: aggregated.guyConfidence,
          momentum: aggregated.momentum,
          toolUsage: aggregated.toolUsage,
          agentHandoffs: aggregated.agentHandoffs
        });
        setLoading(false);

      } catch (err) {
        console.error('Error fetching Weave data:', err);
        setLoading(false);
      }
    };

    fetchWeaveData();
    const interval = setInterval(fetchWeaveData, 5000);
    return () => clearInterval(interval);
  }, []);

  const currentMetrics = metrics;

  const radarData = {
    labels: ['Joy', 'Curiosity', 'Nervousness'],
    datasets: [
      {
        label: 'Girl AI',
        data: [
          currentMetrics.emotions.girl.joy,
          currentMetrics.emotions.girl.curiosity,
          currentMetrics.emotions.girl.nervousness,
        ],
        backgroundColor: 'rgba(255, 182, 193, 0.5)',
        borderColor: '#ff6b81',
        borderWidth: 2,
        pointBackgroundColor: '#ff6b81',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#ff6b81',
      },
      {
        label: 'Guy AI',
        data: [
          currentMetrics.emotions.guy.joy,
          currentMetrics.emotions.guy.curiosity,
          currentMetrics.emotions.guy.nervousness,
        ],
        backgroundColor: 'rgba(173, 216, 230, 0.5)',
        borderColor: '#70a1ff',
        borderWidth: 2,
        pointBackgroundColor: '#70a1ff',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#70a1ff',
      },
    ],
  };

  const radarOptions = {
    scales: {
      r: {
        angleLines: { color: 'rgba(0, 0, 0, 0.1)' },
        grid: { color: 'rgba(0, 0, 0, 0.1)' },
        pointLabels: {
          font: { family: "'VT323', monospace", size: 16 },
          color: '#1a1a1a'
        },
        ticks: {
          display: false,
          min: 0,
          max: 1,
          stepSize: 0.2
        },
      },
    },
    plugins: {
      legend: {
        position: 'top',
        labels: { font: { family: "'VT323', monospace", size: 18 }, color: '#1a1a1a' }
      }
    },
    maintainAspectRatio: false
  };

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="dashboard-container">
      <img src="/cat.gif" alt="Cat companion left" className="cat-gif cat-left" />
      <img src="/cat.gif" alt="Cat companion right" className="cat-gif cat-right" />
      <h1 className="pixel-header">
        <img src="/heart.png" alt="Love icon" className="heart-icon" />
        Amour.exe
      </h1>

      <div className="dashboard-grid">
        {/* Stats Panel */}
        <div className="pixel-box stats-panel">
          <h2>[ Stats ]</h2>
          <div className="stat-item">
             <span className="stat-label">Girl Interest:</span>
             <span className="stat-value" style={{ color: '#ff6f91' }}>{((currentMetrics.girlInterest || 0) * 100).toFixed(1)}%</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Guy Confidence:</span>
             <span className="stat-value" style={{ color: '#2ecc71' }}>{((currentMetrics.guyConfidence ?? 1) * 100).toFixed(1)}%</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Emotional Momentum:</span>
             <span className="stat-value">{(currentMetrics.momentum >= 0 ? '+' : '')}{currentMetrics.momentum.toFixed(2)}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Total Duration:</span>
             <span className="stat-value">{formatDuration(currentMetrics.duration)}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Handoffs (Girl AI):</span>
             <span className="stat-value">{currentMetrics.handoffs.girl}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Handoffs (Guy AI):</span>
             <span className="stat-value">{currentMetrics.handoffs.guy}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Word Count (Girl AI):</span>
             <span className="stat-value">{currentMetrics.wordCount.girl}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Word Count (Guy AI):</span>
             <span className="stat-value">{currentMetrics.wordCount.guy}</span>
          </div>
        </div>

        {/* Help Agents Panel */}
        <div className="pixel-box stats-panel">
          <h2>[ Agent Help ]</h2>
          <div className="stat-item">
             <span className="stat-label">Memory Access:</span>
             <span className="stat-value">{currentMetrics.toolUsage.memory}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Seduction Coaching:</span>
             <span className="stat-value">{currentMetrics.toolUsage.seduction}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Web Search Usage:</span>
             <span className="stat-value">{currentMetrics.toolUsage.web_search}</span>
          </div>
          <div style={{ marginTop: '10px', borderTop: '1px dashed #ccc', paddingTop: '10px' }}>
            <span className="stat-label" style={{ fontWeight: 'bold' }}>Agent Handoffs:</span>
            {Object.entries(currentMetrics.agentHandoffs).length === 0 ? (
              <div className="stat-item"><span className="stat-label">None</span></div>
            ) : (
              Object.entries(currentMetrics.agentHandoffs).map(([agent, count]) => (
                <div key={agent} className="stat-item">
                  <span className="stat-label">{agent}:</span>
                  <span className="stat-value">{count}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Spider Web Chart Panel */}
        <div className="pixel-box">
          <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>[ Emotions ]</h2>
          <div className="chart-panel">
             <div className="radar-chart-container">
               <Radar data={radarData} options={radarOptions} />
             </div>
          </div>
        </div>
      </div>

      {/* Relationship Progression Tracker */}
      <div className="pixel-box">
        <h2 style={{ textAlign: 'center', marginBottom: '10px' }}>[ Relationship Progression ]</h2>
        <div className="progression-tracker">
           <div className="tracker-line"></div>
           {STAGES.map((stage, index) => {
             const currentIndex = STAGES.indexOf(currentMetrics.stage);
             let className = "tracker-stage";
             if (index === currentIndex) className += " active";
             else if (index < currentIndex) className += " past";

             return (
               <div key={stage} className={className}>
                 {stage}
               </div>
             );
           })}
        </div>
      </div>

    </div>
  );
}

export default App;
