import Layout from "../components/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import {
  ExternalLink,
  FileText,
  MapPin,
  Mail,
  Bus,
  ShieldCheck,
} from "lucide-react";

const PAYSTUB_URL = "https://ghservicegroup.madisonrf.com";
const PAYROLL_EMAIL = "payroll@ghsgroup.com";

const Resources = () => (
  <Layout>
    <div className="max-w-2xl mx-auto space-y-5 p-4 pb-28 lg:pb-8">
      <header>
        <p className="text-sm text-muted-foreground">Employee resources</p>
        <h1 className="font-serif text-3xl font-bold text-foundation">
          Help & Paystubs
        </h1>
      </header>

      <Card className="bg-white border-0 shadow-lg overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-foundation via-keystone to-amber-500" />
        <CardHeader>
          <CardTitle className="font-serif text-xl flex items-center gap-2 text-foundation">
            <FileText className="w-5 h-5 text-keystone" />
            Madison Paystub Portal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            View paystubs, review year-to-date information, and update your
            portal email or password.
          </p>
          <div className="rounded-lg bg-horizon p-3 text-sm text-foundation">
            <p><strong>First username:</strong> Last name + last 4 digits of SSN</p>
            <p><strong>First password:</strong> Last 4 digits of SSN</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Change your password after signing in. Never share SSN digits,
              passwords, or PINs by group text.
            </p>
          </div>
          <Button asChild className="w-full h-12 bg-keystone hover:bg-keystone/90">
            <a href={PAYSTUB_URL} target="_blank" rel="noreferrer">
              Open Paystub Portal <ExternalLink className="w-4 h-4 ml-2" />
            </a>
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-white border-0 shadow-md">
        <CardHeader>
          <CardTitle className="font-serif text-xl flex items-center gap-2 text-foundation">
            <Bus className="w-5 h-5 text-keystone" />
            Brownsville Workday Sequence
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3 text-sm">
            {[
              ["Check In for Shuttle", "Attendance at Browne only; paid time has not started."],
              ["Start Work", "Begins paid time at the scheduled shift start."],
              ["Lunch Out / Lunch In", "Records the actual meal break."],
              ["End Work", "Ends paid work time."],
              ["Check Out at Browne", "Return confirmation only; does not change paid hours."],
            ].map(([title, detail], index) => (
              <li key={title} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-keystone/10 text-keystone font-bold flex items-center justify-center shrink-0">
                  {index + 1}
                </span>
                <span>
                  <strong className="text-foundation">{title}</strong>
                  <span className="block text-muted-foreground">{detail}</span>
                </span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="bg-white border-0 shadow-sm">
          <CardContent className="p-5">
            <MapPin className="w-6 h-6 text-keystone mb-3" />
            <p className="font-semibold text-foundation">Browne shuttle lot</p>
            <p className="text-sm text-muted-foreground mt-1">
              109 N Browne Ave<br />Brownsville, TX 78521
            </p>
            <p className="text-xs text-muted-foreground mt-3">
              Turn left after entering. Look for the ABM trailer near the white
              shuttle buses.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-0 shadow-sm">
          <CardContent className="p-5">
            <Mail className="w-6 h-6 text-keystone mb-3" />
            <p className="font-semibold text-foundation">Payroll support</p>
            <p className="text-sm text-muted-foreground mt-1">
              Report missing hours or pay discrepancies promptly.
            </p>
            <a
              href={`mailto:${PAYROLL_EMAIL}`}
              className="inline-flex items-center text-sm font-medium text-keystone mt-3 hover:underline"
            >
              {PAYROLL_EMAIL}
            </a>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-foundation text-white border-0 shadow-md">
        <CardContent className="p-5 flex gap-3">
          <ShieldCheck className="w-6 h-6 text-amber-300 shrink-0" />
          <div>
            <p className="font-semibold">If a punch does not confirm</p>
            <p className="text-sm text-white/75 mt-1">
              Take a screenshot, write down the actual time, and contact your
              GHSG lead immediately. Do not repeat punches until you know the
              first attempt failed.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  </Layout>
);

export default Resources;
