import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../lib/auth";
import { useToast } from "../lib/toast";

export function AuthPage() {
  const nav = useNavigate();
  const { login, register, user } = useAuth();
  const { toast } = useToast();

  const [mode, setMode] = React.useState<"login" | "register">("login");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [name, setName] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (user) nav("/projects");
  }, [user, nav]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name);
      toast({ title: "Success", description: "Signed in." });
      nav("/projects");
    } catch (err: any) {
      toast({ title: "Auth failed", description: err?.message || "Error", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-12">
        <div>
          <div className="text-2xl font-bold">Manuscript Writer</div>
          <div className="text-sm text-slate-600">Clinical/HEOR manuscript workflow.</div>
        </div>
        <Card>
          <div className="mb-3 flex gap-2">
            <Button variant={mode === "login" ? "default" : "outline"} onClick={() => setMode("login")} type="button">
              Login
            </Button>
            <Button
              variant={mode === "register" ? "default" : "outline"}
              onClick={() => setMode("register")}
              type="button"
            >
              Register
            </Button>
          </div>
          <form className="flex flex-col gap-3" onSubmit={onSubmit}>
            {mode === "register" ? (
              <div>
                <div className="mb-1 text-sm font-medium">Name</div>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
              </div>
            ) : null}
            <div>
              <div className="mb-1 text-sm font-medium">Email</div>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@org.com" />
            </div>
            <div>
              <div className="mb-1 text-sm font-medium">Password</div>
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                type="password"
              />
            </div>
            <Button disabled={loading} type="submit">
              {loading ? "Working..." : mode === "login" ? "Login" : "Create account"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

