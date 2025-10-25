import { render, screen, waitFor } from '@testing-library/react';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

vi.mock('../api/client', () => ({
  getSnapshots: async () => [
    { timestamp: 1700000000, pad: [0.6, 0.4, 0.5], entropy: 0.3, coherence: 0.7, samples: 10, tone: 'warm' },
    { timestamp: 1700000300, pad: [0.62, 0.41, 0.5], entropy: 0.32, coherence: 0.68, samples: 20, tone: 'warm' },
  ],
  getTrends: async () => ({
    entropy_trend: 'increasing',
    coherence_trend: 'decreasing',
    overall_mood: 'positive',
    entropy_change: 0.02,
    coherence_change: -0.02,
  }),
}));

describe('AnalyticsDashboard', () => {
  it('renders trend summary', async () => {
    render(<AnalyticsDashboard />);
    await waitFor(() => screen.getByText(/Analytics/i));
    expect(screen.getByText(/Overall mood/i)).toBeInTheDocument();
    expect(screen.getByText('positive')).toBeInTheDocument();
  });
});

