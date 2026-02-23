import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Clock, Users, FileCheck, CheckCircle2, XCircle, 
  Eye, Loader2, MapPin, AlertCircle
} from "lucide-react";

const ManagerDashboard = () => {
  const { user } = useAuth();
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [teamStatus, setTeamStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [pendingRes, teamRes] = await Promise.all([
        axios.get(`${API}/manager/pending`),
        axios.get(`${API}/manager/team`)
      ]);
      setPendingTimesheets(pendingRes.data);
      setTeamStatus(teamRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (timesheetId, action) => {
    setProcessingId(timesheetId);
    try {
      await axios.post(`${API}/timesheets/${timesheetId}/approve`, {
        timesheet_id: timesheetId,
        action,
        notes: null
      });
      
      toast.success(`Timesheet ${action === "approve" ? "approved" : "rejected"}`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to process approval");
    } finally {
      setProcessingId(null);
    }
  };

  const handleSyncToSheets = async (timesheetId) => {
    try {
      await axios.post(`${API}/sheets/sync`, null, {
        params: { timesheet_id: timesheetId }
      });
      toast.success("Synced to Google Sheets");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to sync");
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  const clockedInCount = teamStatus.filter(t => t.is_clocked_in).length;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* Header */}
        <div>
          <h1 className="font-heading text-3xl font-bold">Manager Dashboard</h1>
          <p className="text-muted-foreground">Team oversight and timesheet approvals</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="bg-card border-border border-t-2 border-t-primary">
            <CardContent className="p-4 text-center">
              <FileCheck className="w-6 h-6 mx-auto mb-2 text-primary" />
              <p className="font-mono text-3xl font-bold">{pendingTimesheets.length}</p>
              <p className="text-xs text-muted-foreground">Pending Approvals</p>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border border-t-2 border-t-success">
            <CardContent className="p-4 text-center">
              <Users className="w-6 h-6 mx-auto mb-2 text-success" />
              <p className="font-mono text-3xl font-bold">{clockedInCount}</p>
              <p className="text-xs text-muted-foreground">Clocked In</p>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border border-t-2 border-t-secondary">
            <CardContent className="p-4 text-center">
              <Clock className="w-6 h-6 mx-auto mb-2 text-secondary" />
              <p className="font-mono text-3xl font-bold">{teamStatus.length}</p>
              <p className="text-xs text-muted-foreground">Team Members</p>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <MapPin className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
              <p className="font-mono text-3xl font-bold">{user?.assigned_sites?.length || 0}</p>
              <p className="text-xs text-muted-foreground">Assigned Sites</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="pending" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="pending" className="flex items-center gap-2">
              <FileCheck className="w-4 h-4" />
              Pending ({pendingTimesheets.length})
            </TabsTrigger>
            <TabsTrigger value="team" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Team Status
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pending" className="mt-6 space-y-4">
            {pendingTimesheets.length === 0 ? (
              <Card className="bg-card border-border">
                <CardContent className="py-12 text-center">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-success opacity-50" />
                  <p className="text-muted-foreground">No pending timesheets</p>
                </CardContent>
              </Card>
            ) : (
              pendingTimesheets.map((ts) => (
                <Card key={ts.timesheet_id} className="bg-card border-border card-interactive">
                  <CardContent className="p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                          {ts.employee?.picture ? (
                            <img src={ts.employee.picture} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <Users className="w-5 h-5 text-muted-foreground" />
                          )}
                        </div>
                        <div>
                          <p className="font-semibold">{ts.employee?.name || "Unknown"}</p>
                          <p className="text-sm text-muted-foreground">
                            {ts.site?.name || "Unknown Site"}
                          </p>
                          <p className="text-xs text-muted-foreground font-mono mt-1">
                            {format(new Date(ts.week_start), "MMM d")} - {format(new Date(ts.week_end), "MMM d, yyyy")}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex flex-col sm:items-end gap-2">
                        <div className="text-right">
                          <p className="font-mono text-2xl font-bold text-primary">
                            {ts.total_hours?.toFixed(2)}h
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {ts.entries?.length || 0} entries
                          </p>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button
                            data-testid={`view-timesheet-${ts.timesheet_id}`}
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(`/approve/${ts.timesheet_id}?token=${ts.approval_token}`, '_blank')}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                          <Button
                            data-testid={`approve-${ts.timesheet_id}`}
                            size="sm"
                            onClick={() => handleApproval(ts.timesheet_id, "approve")}
                            disabled={processingId === ts.timesheet_id}
                            className="bg-success hover:bg-success/90"
                          >
                            {processingId === ts.timesheet_id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <CheckCircle2 className="w-4 h-4 mr-1" />
                            )}
                            Approve
                          </Button>
                          <Button
                            data-testid={`reject-${ts.timesheet_id}`}
                            variant="destructive"
                            size="sm"
                            onClick={() => handleApproval(ts.timesheet_id, "reject")}
                            disabled={processingId === ts.timesheet_id}
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="team" className="mt-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {teamStatus.map((member) => (
                <Card key={member.employee?.user_id} className="bg-card border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                          {member.employee?.picture ? (
                            <img src={member.employee.picture} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <Users className="w-6 h-6 text-muted-foreground" />
                          )}
                        </div>
                        <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-card ${
                          member.is_clocked_in ? "bg-success glow-success" : "bg-muted"
                        }`}></div>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold truncate">{member.employee?.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">
                          {member.employee?.numeric_id || "No ID"}
                        </p>
                      </div>
                      
                      <Badge variant={member.is_clocked_in ? "default" : "secondary"}>
                        {member.is_clocked_in ? "Active" : "Off"}
                      </Badge>
                    </div>
                    
                    {member.is_clocked_in && member.current_entry && (
                      <div className="mt-3 pt-3 border-t border-border">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Since</span>
                          <span className="font-mono">
                            {format(new Date(member.current_entry.clock_in), "HH:mm")}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 mt-1">
                          {member.current_entry.location_verified ? (
                            <Badge variant="outline" className="text-xs text-success border-success">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              On-site
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs text-destructive border-destructive">
                              <AlertCircle className="w-3 h-3 mr-1" />
                              Off-site
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              
              {teamStatus.length === 0 && (
                <Card className="bg-card border-border col-span-full">
                  <CardContent className="py-12 text-center">
                    <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">No team members assigned</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default ManagerDashboard;
