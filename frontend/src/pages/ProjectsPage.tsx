import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "../lib/toast";

type Project = {
  id: string;
  title: string;
  description?: string | null;
  status: string;
  updated_at: string;
};

export function ProjectsPage() {
  const { logout, user } = useAuth();
  const { toast } = useToast();
  const [projects, setProjects] = React.useState<Project[]>([]);
  const [loading, setLoading] = React.useState(true);

  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");

  async function refresh() {
    setLoading(true);
    try {
      const data = await apiFetch<Project[]>("/api/projects");
      setProjects(data);
    } catch (err: any) {
      toast({ title: "Failed to load projects", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createProject() {
    try {
      const p = await apiFetch<Project>("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, status: "draft" }),
      });
      setTitle("");
      setDescription("");
      setProjects((prev) => [p, ...prev]);
      toast({ title: "Project created" });
    } catch (err: any) {
      toast({ title: "Create failed", description: err?.message, variant: "destructive" });
    }
  }

  async function deleteProject(id: string) {
    try {
      await apiFetch(`/api/projects/${id}`, { method: "DELETE" });
      setProjects((prev) => prev.filter((p) => p.id !== id));
      toast({ title: "Deleted" });
    } catch (err: any) {
      toast({ title: "Delete failed", description: err?.message, variant: "destructive" });
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-2xl font-bold">Projects</div>
            <div className="text-sm text-slate-600">Signed in as {user?.email}</div>
          </div>
          <Button variant="outline" onClick={logout}>
            Logout
          </Button>
        </div>

        <Card className="flex flex-col gap-3">
          <div className="text-sm font-semibold">New project</div>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Project title" />
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Short description"
            rows={3}
          />
          <div className="flex gap-2">
            <Button onClick={createProject} disabled={!title.trim()}>
              Create
            </Button>
            <Button variant="outline" onClick={refresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        </Card>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {projects.map((p) => (
            <Card key={p.id} className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-lg font-semibold">{p.title}</div>
                  <div className="text-sm text-slate-600">{p.description || "—"}</div>
                </div>
                <Button variant="destructive" onClick={() => deleteProject(p.id)}>
                  Delete
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link to={`/projects/${p.id}/upload`}>
                  <Button variant="outline">Upload report</Button>
                </Link>
                <Link to={`/projects/${p.id}/literature`}>
                  <Button variant="outline">Literature</Button>
                </Link>
                <Link to={`/projects/${p.id}/manuscript`}>
                  <Button>Manuscript</Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>

        {loading && projects.length === 0 ? <div className="text-sm text-slate-600">Loading…</div> : null}
      </div>
    </div>
  );
}

