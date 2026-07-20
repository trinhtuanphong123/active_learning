export function ChapterNav({ chapters }) {
  return (
    <nav className="chapter-nav" aria-label="Explainer chapters">
      {chapters.map((chapter) => (
        <a key={chapter.id} href={`#${chapter.id}`}>
          <span className="chapter-index">{chapter.index}</span>
          <span>{chapter.label}</span>
        </a>
      ))}
    </nav>
  );
}
