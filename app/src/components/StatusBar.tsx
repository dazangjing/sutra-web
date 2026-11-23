import type { Doc } from '../lib/types';

interface Props {
  docCount: number;
  corpus: { docCount: number; assetCount: number; totalChars: number; totalJuan: number } | null;
  currentDoc: Doc | null;
  progress?: number;
}

export default function StatusBar({ docCount, corpus, currentDoc, progress }: Props) {
  return (
    <footer className="statusbar">
      <span>
        篇目 <b>{docCount.toLocaleString('en-US')}</b>
      </span>
      {corpus && (
        <>
          <span>
            卷数 <b>{corpus.totalJuan.toLocaleString('en-US')}</b>
          </span>
          <span>
            正文 <b>{(corpus.totalChars / 10000).toFixed(1)}</b> 万字
          </span>
        </>
      )}
      <span className="statusbar-spacer" />
      {currentDoc ? (
        <>
          <span>
            当前 <b>{currentDoc.title}</b>
          </span>
          <span>
            段 <b>{currentDoc.paragraphs.length}</b>
          </span>
          {progress !== undefined && (
            <span>
              读至 <b>{progress + 1}</b>
            </span>
          )}
        </>
      ) : (
        <span>未选篇目</span>
      )}
      <span>本地语料 · 离线可用</span>
    </footer>
  );
}
