import { useEffect, useRef } from 'react';
import { NeuroFeedbackFrame } from './useNeuroFeedback';

export type AstroFieldState = {
  field_id: string;
  pad_avg: [number, number, number];
  entropy: number;
  coherence: number;
  ts: number;
  samples: number;
};

type AstroHandler = (state: AstroFieldState) => void;

export function useAstroField(frame: NeuroFeedbackFrame | null, onField: AstroHandler) {
  const handlerRef = useRef(onField);

  useEffect(() => {
    handlerRef.current = onField;
  }, [onField]);

  useEffect(() => {
    if (!frame) {
      return;
    }

    handlerRef.current({
      field_id: 'global',
      pad_avg: frame.pad,
      entropy: frame.entropy,
      coherence: frame.coherence,
      ts: frame.ts,
      samples: frame.samples
    });
  }, [frame]);
}
