import { gql, useQuery } from '@apollo/client';
import {
    Chart as ChartJS,
    Filler,
    Legend,
    LineElement,
    PointElement,
    RadialLinearScale,
    Tooltip,
} from 'chart.js';
import { useEffect, useState } from 'react';
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

// Placeholder GraphQL query for W&B Weave API
const GET_AMOUR_METRICS = gql`
  query GetAmourMetrics {
    run(name: "amour-run") {
      history {
        handoffs {
          girl
          guy
        }
        duration
        wordCount {
          girl
          guy
        }
        emotions {
          girl { joy curiosity nervousness }
          guy { joy curiosity nervousness }
        }
        stage
      }
    }
  }
`;

const STAGES = ['Strangers', 'Curious', 'Flirting', 'Couple'];

function App() {
  // Try to use GraphQL for real data (W&B Weave)
  // this is wrapped in try-catch/error-state in reality,
  // we poll every 2s for real-time updates.
  const { data, loading, error } = useQuery(GET_AMOUR_METRICS, {
    pollInterval: 2000,
    // Provide a mocked response on error so it renders the dummy data in the dashboard if the endpoint is completely stubbed
    errorPolicy: 'ignore'
  });

  // Mock data state for demonstration if GraphQL doesn't work/is placeholder
  const [metrics, setMetrics] = useState({
    handoffs: { girl: 12, guy: 15 },
    duration: 120, // seconds
    wordCount: { girl: 450, guy: 380 },
    emotions: {
      girl: { joy: 0.6, curiosity: 0.8, nervousness: 0.4 },
      guy: { joy: 0.5, curiosity: 0.7, nervousness: 0.6 },
    },
    stage: 'Curious'
  });

  // Simulate real-time updates if using mock data
  useEffect(() => {
    if (!data?.run) {
      const interval = setInterval(() => {
        setMetrics(prev => {
          // Add some jitter to emotions
          const jitter = () => (Math.random() - 0.5) * 0.1;
          const clamp = (v) => Math.max(0, Math.min(1, v));

          let newGirlJoy = clamp(prev.emotions.girl.joy + jitter());
          let newGuyJoy = clamp(prev.emotions.guy.joy + jitter());

          let duration = prev.duration + 2;

          // Basic logic to progress stage mock
          let newStage = prev.stage;
          const stageIndex = STAGES.indexOf(prev.stage);
          if (duration > 300 && newGirlJoy > 0.8 && newGuyJoy > 0.8 && stageIndex < 3) {
             newStage = STAGES[stageIndex+1];
          }

          return {
            ...prev,
            duration: duration,
            emotions: {
              girl: {
                joy: newGirlJoy,
                curiosity: clamp(prev.emotions.girl.curiosity + jitter()),
                nervousness: clamp(prev.emotions.girl.nervousness + jitter()),
              },
              guy: {
                joy: newGuyJoy,
                curiosity: clamp(prev.emotions.guy.curiosity + jitter()),
                nervousness: clamp(prev.emotions.guy.nervousness + jitter()),
              }
            },
            stage: newStage
          };
        });
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [data]);

  // Use actual data if available from GraphQL
  const currentMetrics = data?.run?.history ? data.run.history[data.run.history.length - 1] : metrics;

  // Radar Chart Data formatting
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
          display: false, // hide numbers
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
      <h1 className="pixel-header">AI Love Story</h1>

      <div className="dashboard-grid">
        {/* Stats Panel */}
        <div className="pixel-box stats-panel">
          <h2>[ Stats ]</h2>
          <div className="stat-item">
             <span className="stat-label">Handoffs (Girl AI):</span>
             <span className="stat-value">{currentMetrics.handoffs.girl}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Handoffs (Guy AI):</span>
             <span className="stat-value">{currentMetrics.handoffs.guy}</span>
          </div>
          <div className="stat-item">
             <span className="stat-label">Total Duration:</span>
             <span className="stat-value">{formatDuration(currentMetrics.duration)}</span>
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
