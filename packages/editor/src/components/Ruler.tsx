"use client";
import type { PageMarginsMm } from "@ithute/document-schema";
export function Ruler({ widthMm, margins }: { widthMm: number; margins: PageMarginsMm }) {
  const marks = Array.from({ length: Math.floor(widthMm / 10) + 1 }, (_, i) => i * 10);
  return <div className="ithute-ruler" aria-label="Horizontal ruler">
    <div className="ithute-ruler-margin left" style={{ width: `${(margins.left / widthMm) * 100}%` }} />
    <div className="ithute-ruler-margin right" style={{ width: `${(margins.right / widthMm) * 100}%` }} />
    {marks.map((mm) => <span key={mm} className="ithute-ruler-mark" style={{ left: `${(mm / widthMm) * 100}%` }}><i />{mm % 20 === 0 ? <b>{mm / 10}</b> : null}</span>)}
  </div>;
}
