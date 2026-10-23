import "@testing-library/jest-dom/vitest";
// Recharts needs ResizeObserver in jsdom
class RO { observe() {} unobserve() {} disconnect() {} }
(globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO;
