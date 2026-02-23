import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { format, startOfWeek, endOfWeek, subWeeks, addWeeks } from "date-fns";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { 
  Calendar, ChevronLeft, ChevronRight, Clock, Download, 
  Send, CheckCircle2, XCircle, Loader2, FileSpreadsheet 
} from "lucide-react";

const Timesheet = () => {
  const { user } = useAuth();
  const [entries, setEntries] = useState([]);
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState("");
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }));
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [timesheets, setTimesheets] = useState([]);

  const weekEnd = endOfWeek(weekStart, { weekStartsOn: 1 });

  useEffect(() => {
    const fetchSites = async () => {
      try {
        const response = await axios.get(`${API}/sites`);
        setSites(response.data);
        if (response.data.length > 0 && !selectedSite) {
          setSelectedSite(response.data[0].site_id);
        }
      } catch (error) {
        toast.error("Failed to load sites");
      }
    };
    fetchSites();
  }, []);

  useEffect(() => {
    if (!selectedSite) return;

    const fetchEntries = async () => {
      setLoading(true);
      try {
        const [entriesRes, timesheetsRes] = await Promise.all([
          axios.get(`${API}/entries`, {
            params: {
              start_date: weekStart.toISOString(),
              end_date: weekEnd.toISOString()
            }
          }),
          axios.get(`${API}/timesheets`)
        ]);
        
        // Filter entries for selected site
        const siteEntries = entriesRes.data.filter(e => e.site_id === selectedSite);
        setEntries(siteEntries);
        setTimesheets(timesheetsRes.data);
      } catch (error) {
        toast.error("Failed to load entries");
      } finally {
        setLoading(false);
      }
    };

    fetchEntries();
  }, [selectedSite, weekStart]);

  const navigateWeek = (direction) => {
    setWeekStart(prev => direction === "prev" ? subWeeks(prev, 1) : addWeeks(prev, 1));
  };

  const getTotalHours = () => {
    return entries.reduce((sum, e) => sum + (e.total_hours || 0), 0).toFixed(2);
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: { variant: "default", icon: Clock },
      completed: { variant: "secondary", icon: CheckCircle2 },
      pending_approval: { variant: "outline", icon: Clock },
      approved: { variant: "default", icon: CheckCircle2 },
      rejected: { variant: "destructive", icon: XCircle }
    };
    const config = variants[status] || variants.completed;
    const Icon = config.icon;
    return (
      <Badge variant={config.variant} className="flex items-center gap-1 text-xs">
        <Icon className="w-3 h-3" />
        {status.replace("_", " ")}
      </Badge>
    );
  };

  const currentWeekTimesheet = timesheets.find(ts => 
    ts.site_id === selectedSite &&
    new Date(ts.week_start).toDateString() === weekStart.toDateString()
  );

  const handleSubmit = async () => {
    if (entries.length === 0) {
      toast.error("No entries to submit");
      return;
    }

    const incompleteEntries = entries.filter(e => e.status === "active");
    if (incompleteEntries.length > 0) {
      toast.error("Please clock out from all entries before submitting");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/timesheets/submit`, null, {
        params: {
          week_start: weekStart.toISOString(),
          site_id: selectedSite
        }
      });
      toast.success("Timesheet submitted for approval");
      
      // Refresh timesheets
      const timesheetsRes = await axios.get(`${API}/timesheets`);
      setTimesheets(timesheetsRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit timesheet");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(`${API}/export/csv`, {
        params: {
          start_date: weekStart.toISOString(),
          end_date: weekEnd.toISOString(),
          site_id: selectedSite
        },
        responseType: "blob"
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `timesheet_${format(weekStart, "yyyy-MM-dd")}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("CSV exported successfully");
    } catch (error) {
      toast.error("Failed to export CSV");
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

  return (
    <Layout>
      <div className="max-w-4xl mx-auto p-4 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading text-3xl font-bold">Timesheet</h1>
            <p className="text-muted-foreground">Review and submit your work hours</p>
          </div>
          
          <Select value={selectedSite} onValueChange={setSelectedSite}>
            <SelectTrigger data-testid="timesheet-site-select" className="w-full sm:w-48 bg-card">
              <SelectValue placeholder="Select site" />
            </SelectTrigger>
            <SelectContent>
              {sites.map((site) => (
                <SelectItem key={site.site_id} value={site.site_id}>
                  {site.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Week Navigator */}
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => navigateWeek("prev")}
                data-testid="prev-week-btn"
              >
                <ChevronLeft className="w-5 h-5" />
              </Button>
              
              <div className="text-center">
                <div className="flex items-center gap-2 justify-center">
                  <Calendar className="w-5 h-5 text-primary" />
                  <span className="font-heading text-lg font-semibold">
                    {format(weekStart, "MMM d")} - {format(weekEnd, "MMM d, yyyy")}
                  </span>
                </div>
                {currentWeekTimesheet && (
                  <div className="mt-1">
                    {getStatusBadge(currentWeekTimesheet.status)}
                  </div>
                )}
              </div>
              
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => navigateWeek("next")}
                data-testid="next-week-btn"
              >
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Summary Card */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Total Hours</p>
              <p className="font-mono text-2xl font-bold text-primary">{getTotalHours()}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Entries</p>
              <p className="font-mono text-2xl font-bold">{entries.length}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Verified</p>
              <p className="font-mono text-2xl font-bold text-success">
                {entries.filter(e => e.location_verified).length}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Status</p>
              <p className="font-mono text-lg font-semibold">
                {currentWeekTimesheet?.status?.toUpperCase() || "DRAFT"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Entries Table */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Time Entries
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : entries.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No entries for this week</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table className="data-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Clock In</TableHead>
                      <TableHead>Clock Out</TableHead>
                      <TableHead>Lunch</TableHead>
                      <TableHead>Hours</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.map((entry) => (
                      <TableRow key={entry.entry_id}>
                        <TableCell>{formatDate(entry.clock_in)}</TableCell>
                        <TableCell className="font-mono">{formatTime(entry.clock_in)}</TableCell>
                        <TableCell className="font-mono">{formatTime(entry.clock_out)}</TableCell>
                        <TableCell className="font-mono">
                          {entry.lunch_start && entry.lunch_end 
                            ? `${formatTime(entry.lunch_start)}-${formatTime(entry.lunch_end)}`
                            : "-"
                          }
                        </TableCell>
                        <TableCell className="font-mono font-semibold">
                          {entry.total_hours?.toFixed(2) || "-"}
                        </TableCell>
                        <TableCell>{getStatusBadge(entry.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            data-testid="export-csv-btn"
            variant="outline"
            onClick={handleExport}
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
          
          {!currentWeekTimesheet && entries.length > 0 && (
            <Button
              data-testid="submit-timesheet-btn"
              onClick={handleSubmit}
              disabled={submitting || entries.some(e => e.status === "active")}
              className="flex items-center gap-2 bg-primary glow-primary"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Submit for Approval
            </Button>
          )}
          
          {currentWeekTimesheet?.status === "approved" && (
            <Button
              variant="outline"
              className="flex items-center gap-2 text-success border-success"
              disabled
            >
              <CheckCircle2 className="w-4 h-4" />
              Approved
            </Button>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Timesheet;
