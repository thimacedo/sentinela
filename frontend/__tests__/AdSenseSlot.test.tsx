import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

describe('AdSenseSlot', () => {
  beforeAll(() => {
    // Mock the global adsbygoogle array and push function
    (window as any).adsbygoogle = [];
    (window as any).adsbygoogle.push = jest.fn();
  });

  it('renders ins element with correct attributes', () => {
    const { container } = render(<AdSenseSlot adSlot="2020882637" format="horizontal" />);
    const ins = container.querySelector('ins.adsbygoogle');
    expect(ins).toBeInTheDocument();
    expect(ins).toHaveAttribute('data-ad-client', 'ca-pub-1827611269042960');
    expect(ins).toHaveAttribute('data-ad-slot', '2020882637');
    expect(ins).toHaveAttribute('data-ad-format', 'horizontal');
  });

  it('calls adsbygoogle.push on mount', () => {
    render(<AdSenseSlot adSlot="2020882637" format="horizontal" />);
    expect((window as any).adsbygoogle.push).toHaveBeenCalled();
  });
});
