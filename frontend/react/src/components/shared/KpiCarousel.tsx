import { useState, useRef, useCallback } from "react";

export interface KpiCard {
  id: string;
  label: string;
  value: string;
  subtitle: string;
  accent: string;
  gradientClass: string;
  icon?: string;
  pending?: string | null;
}

export function KpiCarousel({ cards }: { cards: KpiCard[] }) {
  const [activeKpiIndex, setActiveKpiIndex] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);

  const navigateTo = useCallback((index: number) => {
    setActiveKpiIndex(Math.max(0, Math.min(cards.length - 1, index)));
  }, [cards.length]);

  const handleScroll = useCallback(() => {
    const el = carouselRef.current;
    if (!el) return;
    const slideWidth = el.querySelector('.kpi-slide')?.clientWidth ?? el.clientWidth;
    const index = Math.round(el.scrollLeft / slideWidth);
    setActiveKpiIndex(Math.max(0, Math.min(cards.length - 1, index)));
  }, [cards.length]);

  const scrollToCard = useCallback((index: number) => {
    const el = carouselRef.current;
    if (!el) return;
    const slide = el.children[index] as HTMLElement | undefined;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (slide) el.scrollTo({ left: slide.offsetLeft, behavior: reducedMotion ? 'auto' : 'smooth' });
  }, []);

  return (
    <div className="kpi-carousel-wrapper">

      {/* Mobile: native scroll-snap carousel */}
      <div ref={carouselRef} className="kpi-scroller md:hidden" onScroll={handleScroll}>
        {cards.map((card) => (
          <div key={card.id} className={`kpi-slide ${card.gradientClass}`}>
            <div className="kpi-accent" style={{ background: card.accent }} />
            <img
              src="/wallet-mantra-logo.png"
              alt=""
              aria-hidden="true"
              className="kpi-watermark-img"
            />
            <div className="kpi-slide-header">
              {card.icon && <span className="kpi-slide-icon">{card.icon}</span>}
              <span className="kpi-card-label">{card.label}</span>
            </div>
            <p className="kpi-card-value">{card.value}</p>
            <p className="kpi-card-sub">{card.subtitle}</p>
            {card.pending && <p className="kpi-card-pending">{card.pending}</p>}
          </div>
        ))}
      </div>

      {/* Dot indicators — mobile only */}
      <div className="kpi-dots md:hidden">
        {cards.map((card, i) => (
          <button
            key={card.id}
            className={`kpi-dot ${i === activeKpiIndex ? "active" : ""}`}
            onClick={() => scrollToCard(i)}
            aria-label={`View ${card.label}`}
          />
        ))}
      </div>

      {/* Desktop: all cards side by side */}
      <div className="kpi-desktop-row hidden md:flex">
        {cards.map((card, i) => (
          <div
            key={card.id}
            className={`kpi-card-shell ${card.gradientClass} ${i === activeKpiIndex ? "active" : "side"}`}
            style={{ padding: "14px 20px" }}
            onClick={() => navigateTo(i)}
          >
            <div className="kpi-accent" style={{ background: card.accent }} />
            <img
              src="/wallet-mantra-logo.png"
              alt=""
              aria-hidden="true"
              className="kpi-watermark-img"
            />
            <div className="kpi-slide-header" style={{ marginBottom: 10 }}>
              {card.icon && <span className="kpi-slide-icon" style={{ fontSize: 14 }}>{card.icon}</span>}
              <span className="kpi-card-label" style={{ fontSize: 10 }}>{card.label}</span>
            </div>
            <p className="kpi-card-value" style={{ fontSize: 24 }}>{card.value}</p>
            <p className="kpi-card-sub" style={{ fontSize: 10, marginTop: 3 }}>{card.subtitle}</p>
            {card.pending && (
              <p className="kpi-card-pending" style={{ fontSize: 10, marginTop: 2 }}>{card.pending}</p>
            )}
          </div>
        ))}
      </div>

    </div>
  );
}
