import '@testing-library/jest-dom';

class ResizeObserver {
  callback: ResizeObserverCallback;
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }
  observe() {
    // noop
  }
  unobserve() {
    // noop
  }
  disconnect() {
    // noop
  }
}

// @ts-expect-error jsdom polyfill for charts
global.ResizeObserver = ResizeObserver;

