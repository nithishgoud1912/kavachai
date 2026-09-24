"use client";
import type { ArtifactItem } from "@/app/types";
export default function XlsxPreview({ artifact, className = "" }: { artifact: ArtifactItem; className?: string }) {
  return <section className={`p-6 space-y-4 ${className}`}>
    <h2>{artifact.name}</h2>
    <p>{artifact.metadata?.summary || "Open the generated file to inspect its contents."}</p>
    {artifact.metadata?.sections?.map((section, i) => <div key={i}><h3>{section.title}</h3><p className="whitespace-pre-wrap">{section.content}</p></div>)}
    <a className="underline" href={artifact.download_url} download={artifact.name}>Download generated file</a>
    <p>Preview metadata is a summary. The download contains the generated Office document.</p>
  </section>;
}
