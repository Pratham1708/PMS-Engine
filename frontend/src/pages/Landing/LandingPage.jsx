import HeroSection from '../../components/landing/HeroSection';
import LiveMarketPreview from '../../components/landing/LiveMarketPreview';
import WhyUsComparison from '../../components/landing/WhyUsComparison';
import ScreenshotCarousel from '../../components/landing/ScreenshotCarousel';
import PlatformWorkflow from '../../components/landing/PlatformWorkflow';
import InteractiveDemo from '../../components/landing/InteractiveDemo';
import StatisticsSection from '../../components/landing/StatisticsSection';
import TechnologySection from '../../components/landing/TechnologySection';
import LandingFooter from '../../components/landing/LandingFooter';

export default function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg-base)', color: 'var(--color-text-primary)' }}>
      <HeroSection />
      <LiveMarketPreview />
      <WhyUsComparison />
      <ScreenshotCarousel />
      <PlatformWorkflow />
      <InteractiveDemo />
      <StatisticsSection />
      <TechnologySection />
      <LandingFooter />
    </div>
  );
}
