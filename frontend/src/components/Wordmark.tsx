/**
 * Marchio AdFlow in versione wordmark: «ad» in Inter Tight, «flow» in
 * Instrument Serif corsivo (scelta editoriale). `chiaro` per gli sfondi
 * scuri (foto della vetrina, footer).
 */
import stili from "./Wordmark.module.css";

export function Wordmark({
  chiaro = false,
  dimensione = 22,
}: {
  chiaro?: boolean;
  dimensione?: number;
}) {
  return (
    <span
      className={`${stili.wordmark} ${chiaro ? stili.chiaro : ""}`}
      style={{ fontSize: dimensione }}
    >
      ad<em>flow</em>
    </span>
  );
}
