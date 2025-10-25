import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EmotionPicker from '../components/EmotionPicker';

vi.mock('../api/client', () => ({
  listEmotions: async () => ({
    total: 2,
    categories: { positive: 1, negative: 0, neutral: 1 },
    emotions: [
      { name: 'радость', pad: [0.8, 0.6, 0.6], category: 'positive' },
      { name: 'спокойствие', pad: [0.7, 0.2, 0.7], category: 'neutral' },
    ],
  }),
  suggestEmotions: async (q: string) =>
    q ? [{ name: 'радость', pad: [0.8, 0.6, 0.6], category: 'positive' }] : [],
}));

describe('EmotionPicker', () => {
  it('renders and selects from suggestions', async () => {
    const onChange = vi.fn();
    render(<EmotionPicker value="" onChange={onChange} />);

    const input = screen.getByPlaceholderText('Emotion');
    fireEvent.change(input, { target: { value: 'рад' } });

    await waitFor(() => screen.getByText('радость'));
    fireEvent.mouseDown(screen.getByText('радость'));

    expect(onChange).toHaveBeenCalledWith('радость', [0.8, 0.6, 0.6]);
  });
});

