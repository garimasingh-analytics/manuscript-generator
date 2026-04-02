import React from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Textarea } from "../components/ui/textarea";
import { apiFetch } from "../lib/api";
import { useToast } from "../lib/toast";

type JobStatus = "queued" | "running" | "completed" | "failed";

export function ManuscriptPage() {
  const { projectId } = useParams();
  const { toast } = useToast();

  const [project, setProject] = React.useState<any>(null);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [jobStatus, setJobStatus] = React.useState<JobStatus | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function loadProject() {
    if (!projectId) return;
    const p = await apiFetch<any>(`/api/projects/${projectId}`);
    setProject(p);
  }

  React.useEffect(() => {
    loadProject().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function start() {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await apiFetch<{ job_id: string; status: JobStatus }>(`/api/agents/generate-manuscript/${projectId}`, {
        method: "POST"
      });
      setJobId(res.job_id);
      setJobStatus(res.status);
      toast({ title: "Generation started", description: "Polling every 2 seconds." });
    } catch (err: any) {
      toast({ title: "Generation failed to start", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    if (!jobId) return;
    let alive = true;
    const t = window.setInterval(async () => {
      try {
        const st = await apiFetch<any>(`/api/agents/generation-status/${jobId}`);
        if (!alive) return;
        setJobStatus(st.status);
        if (st.status === "completed") {
          window.clearInterval(t);
          await loadProject();
          toast({ title: "Manuscript ready" });
        }
        if (st.status === "failed") {
          window.clearInterval(t);
          toast({ title: "Generation failed", description: st.error || "Error", variant: "destructive" });
        }
      } catch {
        // ignore transient polling failures
      }
    }, 2000);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const selectedCount = (project?.papers || []).filter((p: any) => p.selected).length;
  const manuscript = project?.manuscript || {};

  function exportUrl(fmt: string) {
    const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
    return `${base}/api/export/${fmt}/${projectId}`;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">Manuscript</div>
            <div className="text-sm text-slate-600">Project {projectId}</div>
          </div>
          <Link to="/projects">
            <Button variant="outline">Back</Button>
          </Link>
        </div>

        <Card className="flex flex-col gap-2">
          <div className="text-sm text-slate-700">
            Selected papers: <span className="font-semibold">{selectedCount}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={start} disabled={loading || selectedCount === 0}>
              {loading ? "Starting…" : "Generate manuscript"}
            </Button>
            {jobStatus ? <div className="self-center text-sm text-slate-600">Status: {jobStatus}</div> : null}
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            <a href={exportUrl("pdf")}>
              <Button variant="outline">Export PDF</Button>
            </a>
            <a href={exportUrl("docx")}>
              <Button variant="outline">Export DOCX</Button>
            </a>
            <a href={exportUrl("markdown")}>
              <Button variant="outline">Export Markdown</Button>
            </a>
            <a href={exportUrl("references-json")}>
              <Button variant="outline">Refs JSON</Button>
            </a>
            <a href={exportUrl("references-csv")}>
              <Button variant="outline">Refs CSV</Button>
            </a>
          </div>
        </Card>

        <div className="grid grid-cols-1 gap-3">
          {[
            ["Title", "title"],
            ["Abstract", "abstract"],
            ["Introduction", "introduction"],
            ["Methods", "methods"],
            ["Results", "results"],
            ["Evidence Comparison", "evidence_comparison"],
            ["Discussion", "discussion"],
            ["Conclusion", "conclusion"],
          ].map(([label, key]) => (
            <Card key={key}>
              <div className="mb-2 text-sm font-semibold">{label}</div>
              <Textarea value={manuscript?.[key] || ""} readOnly rows={6} />
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

