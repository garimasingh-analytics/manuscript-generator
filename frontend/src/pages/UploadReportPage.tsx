import React from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { apiFetch } from "../lib/api";
import { useToast } from "../lib/toast";

export function UploadReportPage() {
  const { projectId } = useParams();
  const { toast } = useToast();
  const [file, setFile] = React.useState<File | null>(null);
  const [studySummary, setStudySummary] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);

  async function upload() {
    if (!projectId || !file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch<any>(`/api/agents/parse-report/${projectId}`, {
        method: "POST",
        body: form,
        headers: {},
      });
      setStudySummary(res.study_summary);
      toast({ title: "Report parsed", description: "Study summary updated." });
    } catch (err: any) {
      toast({ title: "Upload failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-4xl flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">Upload Report</div>
            <div className="text-sm text-slate-600">Project {projectId}</div>
          </div>
          <Link to="/projects">
            <Button variant="outline">Back</Button>
          </Link>
        </div>

        <Card className="flex flex-col gap-3">
          <input
            type="file"
            accept=".pdf,.docx,.txt,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <div className="flex gap-2">
            <Button onClick={upload} disabled={!file || loading}>
              {loading ? "Parsing…" : "Upload & Parse"}
            </Button>
            <Link to={`/projects/${projectId}/literature`}>
              <Button variant="outline">Next: Literature</Button>
            </Link>
          </div>
        </Card>

        {studySummary ? (
          <Card>
            <div className="text-sm font-semibold">Extracted Study Summary</div>
            <pre className="mt-2 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-50">
              {JSON.stringify(studySummary, null, 2)}
            </pre>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

