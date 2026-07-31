import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { API } from "../App";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  CheckCircle2,
  XCircle,
  Clock,
  MapPin,
  User,
  Calendar,
  Loader2,
  FileText,
  Camera,
} from "lucide-react";

const Brand = () => (
  <div className="inline-flex items-center gap-3" aria-label="GH Service Group">
    <div className="w-12 h-12 rounded-xl bg-keystone text-white flex items-center justify-center font-black">
      GH
    </div>
    <div className="text-left leading-tight">
      <div className="font-serif text-xl font-bold text-foundation">
        GH Service Group
      </div>
      <div className="text-xs uppercase tracking-widest text-foundation/50">
        Workforce Portal
      </div>
    </div>
  </div>
);

const ApprovalPage = () => {
  const { timesheetId } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [notes, setNotes] = useState("");
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    const fetchTimesheet = async () => {
      try {
        const response = await axios.get(`${API}/timesheets/${timesheetId}`, {
          params: { token },
        });
        setData(response.data);

        if (response.data.timesheet?.status !== "submitted") {
          setCompleted(true);
        }
      } catch (error) {
        toast.error(error.response?.data?.detail || "Failed to load timesheet");
      } finally {
        setLoading(false);
      }
    };

    fetchTimesheet();
  }, [timesheetId, token]);

  const handleApproval = async (action) => {
    setProcessing(true);
    try {
      await axios.post(
        `${API}/timesheets/${timesheetId}/approve`,
        {
          timesheet_id: timesheetId,
          action,
          notes: notes || null,
        },
        {
          params: { token },
        },
      );

      toast.success(
        `Timesheet ${action === "approve" ? "approved" : "rejected"}`,
      );
      setCompleted(true);

      // Refresh data
      const response = await axios.get(`${API}/timesheets/${timesheetId}`, {
        params: { token },
      });
      setData(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to process approval");
    } finally {
      setProcessing(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return "-";
    return format(new Date(isoString), "HH:mm");
  };

  const formatDate = (isoString) => {
    if (!isoString) return "-";
    return format(new Date(isoString), "EEE, MMM d");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-horizon flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-keystone mx-auto mb-4" />
          <p className="text-muted-foreground">Loading timesheet...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-horizon flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-white border-0 shadow-lg">
          <CardContent className="py-12 text-center">
            <XCircle className="w-16 h-16 mx-auto mb-4 text-vertex" />
            <h2 className="font-serif text-2xl font-bold text-foundation mb-2">
              Timesheet Not Found
            </h2>
            <p className="text-muted-foreground">
              This timesheet may have been deleted or the link is invalid.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { timesheet, entries, employee, site } = data;

  const getStatusBadge = (status) => {
    const config = {
      submitted: {
        variant: "outline",
        className: "border-keystone text-keystone",
      },
      approved: { variant: "default", className: "bg-green-500" },
      rejected: { variant: "destructive", className: "" },
    };
    const c = config[status] || config.submitted;
    return (
      <Badge variant={c.variant} className={c.className}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-horizon p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center py-6">
          <Brand />
          <p className="text-muted-foreground mt-3">Timesheet Approval</p>
        </div>

        {/* Status Banner */}
        {completed && (
          <Card
            className={`border-2 shadow-md ${
              timesheet.status === "approved"
                ? "border-green-500 bg-green-50"
                : timesheet.status === "rejected"
                  ? "border-vertex bg-red-50"
                  : "border-keystone bg-indigo-50"
            }`}
          >
            <CardContent className="py-4 text-center">
              {timesheet.status === "approved" ? (
                <div className="flex items-center justify-center gap-2 text-green-600">
                  <CheckCircle2 className="w-6 h-6" />
                  <span className="font-serif text-xl">Timesheet Approved</span>
                </div>
              ) : timesheet.status === "rejected" ? (
                <div className="flex items-center justify-center gap-2 text-vertex">
                  <XCircle className="w-6 h-6" />
                  <span className="font-serif text-xl">Timesheet Rejected</span>
                </div>
              ) : null}
              {timesheet.notes && (
                <p className="text-sm mt-2 text-muted-foreground">
                  Note: {timesheet.notes}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Employee Info */}
        <Card className="bg-white border-0 shadow-md">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-keystone/10 flex items-center justify-center overflow-hidden">
                {employee?.picture ? (
                  <img
                    src={employee.picture}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-8 h-8 text-keystone" />
                )}
              </div>

              <div className="flex-1">
                <h2 className="font-serif text-2xl font-bold text-foundation">
                  {employee?.name || "Unknown Employee"}
                </h2>
                <div className="flex flex-wrap gap-4 mt-2 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {site?.name || "Unknown Site"}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {format(new Date(timesheet.week_start), "MMM d")} -{" "}
                    {format(new Date(timesheet.week_end), "MMM d, yyyy")}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <p className="font-mono text-4xl font-bold text-keystone">
                  {timesheet.total_hours?.toFixed(2)}h
                </p>
                <p className="text-sm text-muted-foreground">
                  {entries?.length || 0} entries
                </p>
                <div className="mt-2">{getStatusBadge(timesheet.status)}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Entries Table */}
        <Card className="bg-white border-0 shadow-md">
          <CardHeader>
            <CardTitle className="font-serif text-xl flex items-center gap-2 text-foundation">
              <Clock className="w-5 h-5 text-keystone" />
              Time Entries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Clock In</TableHead>
                    <TableHead>Clock Out</TableHead>
                    <TableHead>Lunch</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Photo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries?.map((entry) => (
                    <TableRow key={entry.entry_id}>
                      <TableCell className="font-medium">
                        {formatDate(entry.clock_in)}
                      </TableCell>
                      <TableCell className="font-mono">
                        {formatTime(entry.clock_in)}
                      </TableCell>
                      <TableCell className="font-mono">
                        {formatTime(entry.clock_out)}
                      </TableCell>
                      <TableCell className="font-mono">
                        {entry.lunch_start && entry.lunch_end
                          ? `${formatTime(entry.lunch_start)}-${formatTime(entry.lunch_end)}`
                          : "-"}
                      </TableCell>
                      <TableCell className="font-mono font-semibold">
                        {entry.total_hours?.toFixed(2) || "-"}
                      </TableCell>
                      <TableCell>
                        {entry.location_verified ? (
                          <Badge
                            variant="outline"
                            className="text-xs text-green-600 border-green-600"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verified
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="text-xs text-vertex border-vertex"
                          >
                            <XCircle className="w-3 h-3 mr-1" />
                            Off-site
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {entry.clock_in_photo ? (
                          <Badge
                            variant="outline"
                            className="text-xs text-keystone"
                          >
                            <Camera className="w-3 h-3 mr-1" />
                            Yes
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Approval Actions */}
        {!completed && timesheet.status === "submitted" && (
          <Card className="bg-white border-0 shadow-md">
            <CardHeader>
              <CardTitle className="font-serif text-xl flex items-center gap-2 text-foundation">
                <FileText className="w-5 h-5 text-keystone" />
                Manager Review
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground">
                  Notes (optional)
                </label>
                <Textarea
                  data-testid="approval-notes"
                  placeholder="Add any notes or corrections..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="mt-1 bg-horizon border-gray-200"
                />
              </div>

              <div className="flex gap-3">
                <Button
                  data-testid="approve-btn"
                  onClick={() => handleApproval("approve")}
                  disabled={processing}
                  className="flex-1 bg-green-500 hover:bg-green-600"
                >
                  {processing ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Approve Timesheet
                </Button>

                <Button
                  data-testid="reject-btn"
                  onClick={() => handleApproval("reject")}
                  disabled={processing}
                  className="flex-1 bg-vertex hover:bg-vertex/90"
                >
                  {processing ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <XCircle className="w-4 h-4 mr-2" />
                  )}
                  Reject Timesheet
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center py-4 space-y-2">
          <p className="text-xs text-muted-foreground italic font-serif">
            "Strengthening communities, one person at a time."
          </p>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Garza Group Recruiting Services, LLC
          </p>
        </div>
      </div>
    </div>
  );
};

export default ApprovalPage;
