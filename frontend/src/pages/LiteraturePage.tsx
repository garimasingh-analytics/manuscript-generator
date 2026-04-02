import React from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { apiFetch } from "../lib/api";
import { useToast } from "../lib/toast";

type Paper = {
  title: string;
  authors?: string[];
  year?: number | null;
  journal?: string | null;
  doi?: string | null;
  pmid?: string | null;
  abstract?: string | null;
  selected?: boolean;
  classification?: "supporting" | "contradicting" | "background" | null;
  database_source?: string | null;
};

export function LiteraturePage() {
  const { projectId } = useParams();
  const { toast } = useToast();

  const [mainKeywords, setMainKeywords] = React.useState("heart failure; dapagliflozin");
  const [exclusionKeywords, setExclusionKeywords] = React.useState("");
  const [meshTerms, setMeshTerms] = React.useState("");
  const [papers, setPapers] = React.useState<Paper[]>([]);
  const [loading, setLoading] = React.useState(false);

  async function search() {
    if (!projectId) return;
    setLoading(true);
    try {
      const payload = {
        databases: ["pubmed", "pmc", "europe_pmc", "semantic_scholar", "crossref", "doaj", "biorxiv", "medrxiv"],
        max_results_per_db: 20,
        main_keywords: mainKeywords.split(";").map((s) => s.trim()).filter(Boolean),
        exclusion_keywords: exclusionKeywords.split(";").map((s) => s.trim()).filter(Boolean),
        mesh_terms: meshTerms.split(";").map((s) => s.trim()).filter(Boolean),
        year_range: { start: 2015, end: 2026 },
        open_access_only: false,
        article_types: [],
      };
      const res = await apiFetch<any>(`/api/agents/search-literature/${projectId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setPapers(res.papers || []);
      toast({ title: "Search complete", description: `Found ${res.total_after_dedupe} papers (deduped).` });
    } catch (err: any) {
      toast({ title: "Search failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  async function saveSelection() {
    if (!projectId) return;
    try {
      await apiFetch<any>(`/api/projects/${projectId}/papers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ papers }),
      });
      toast({ title: "Saved", description: "Selections and classifications persisted." });
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message, variant: "destructive" });
    }
  }

  function toggleSelected(idx: number) {
    setPapers((prev) => prev.map((p, i) => (i === idx ? { ...p, selected: !p.selected } : p)));
  }

  function setClass(idx: number, c: Paper["classification"]) {
    setPapers((prev) => prev.map((p, i) => (i === idx ? { ...p, classification: c } : p)));
  }

  const selectedCount = papers.filter((p) => p.selected).length;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">Literature Search</div>
            <div className="text-sm text-slate-600">Project {projectId}</div>
          </div>
          <Link to="/projects">
            <Button variant="outline">Back</Button>
          </Link>
        </div>

        <Card className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div>
            <div className="mb-1 text-sm font-medium">Main keywords (semicolon-separated)</div>
            <Input value={mainKeywords} onChange={(e) => setMainKeywords(e.target.value)} />
          </div>
          <div>
            <div className="mb-1 text-sm font-medium">Exclusion keywords</div>
            <Input value={exclusionKeywords} onChange={(e) => setExclusionKeywords(e.target.value)} />
          </div>
          <div>
            <div className="mb-1 text-sm font-medium">MeSH terms</div>
            <Input value={meshTerms} onChange={(e) => setMeshTerms(e.target.value)} />
          </div>
          <div className="flex gap-2 md:col-span-3">
            <Button onClick={search} disabled={loading}>
              {loading ? "Searching…" : "Search"}
            </Button>
            <Button variant="outline" onClick={saveSelection}>
              Save selection
            </Button>
            <Link to={`/projects/${projectId}/manuscript`}>
              <Button disabled={selectedCount === 0}>Next: Manuscript ({selectedCount} selected)</Button>
            </Link>
          </div>
        </Card>

        <Card>
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm font-semibold">Results</div>
            <div className="text-sm text-slate-600">{selectedCount} selected</div>
          </div>
          <div className="overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b">
                <tr>
                  <th className="p-2">Select</th>
                  <th className="p-2">Title</th>
                  <th className="p-2">Year</th>
                  <th className="p-2">Source</th>
                  <th className="p-2">Class</th>
                </tr>
              </thead>
              <tbody>
                {papers.map((p, idx) => (
                  <tr key={idx} className="border-b align-top">
                    <td className="p-2">
                      <input type="checkbox" checked={!!p.selected} onChange={() => toggleSelected(idx)} />
                    </td>
                    <td className="p-2">
                      <div className="font-medium">{p.title}</div>
                      <div className="text-xs text-slate-600">
                        {(p.authors || []).slice(0, 6).join(", ")} {p.doi ? `• DOI: ${p.doi}` : ""}{" "}
                        {p.pmid ? `• PMID: ${p.pmid}` : ""}
                      </div>
                    </td>
                    <td className="p-2">{p.year ?? "—"}</td>
                    <td className="p-2">{p.database_source ?? "—"}</td>
                    <td className="p-2">
                      <div className="flex flex-col gap-1">
                        <Button
                          type="button"
                          variant={p.classification === "background" ? "default" : "outline"}
                          onClick={() => setClass(idx, "background")}
                        >
                          Background
                        </Button>
                        <Button
                          type="button"
                          variant={p.classification === "supporting" ? "default" : "outline"}
                          onClick={() => setClass(idx, "supporting")}
                        >
                          Supporting
                        </Button>
                        <Button
                          type="button"
                          variant={p.classification === "contradicting" ? "default" : "outline"}
                          onClick={() => setClass(idx, "contradicting")}
                        >
                          Contradicting
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {papers.length === 0 ? (
                  <tr>
                    <td className="p-2 text-slate-600" colSpan={5}>
                      No results yet. Run a search.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

