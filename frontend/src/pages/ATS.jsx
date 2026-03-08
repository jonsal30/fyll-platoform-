import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Briefcase, Plus, Search, Users, ChevronRight, 
  MapPin, Clock, DollarSign, Loader2, Eye, Edit2,
  CheckCircle2, XCircle, Star, Send, UserPlus
} from "lucide-react";

const ATS = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [applicants, setApplicants] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Job form
  const [jobDialogOpen, setJobDialogOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [jobForm, setJobForm] = useState({
    title: "", location: "", department: "", employment_type: "full_time",
    shift: "", pay_rate_min: "", pay_rate_max: "", pay_type: "hourly",
    description: "", requirements: "", positions_available: 1
  });
  const [savingJob, setSavingJob] = useState(false);
  
  // Applicant detail
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [applicantDialogOpen, setApplicantDialogOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [jobsRes, applicantsRes, statsRes] = await Promise.all([
        axios.get(`${API}/ats/jobs`),
        axios.get(`${API}/ats/applicants`),
        axios.get(`${API}/ats/pipeline/stats`)
      ]);
      setJobs(jobsRes.data);
      setApplicants(applicantsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Failed to load ATS data:", error);
    } finally {
      setLoading(false);
    }
  };

  const openJobDialog = (job = null) => {
    if (job) {
      setEditingJob(job);
      setJobForm({
        title: job.title,
        location: job.location,
        department: job.department || "",
        employment_type: job.employment_type,
        shift: job.shift || "",
        pay_rate_min: job.pay_rate_min || "",
        pay_rate_max: job.pay_rate_max || "",
        pay_type: job.pay_type,
        description: job.description,
        requirements: (job.requirements || []).join("\n"),
        positions_available: job.positions_available
      });
    } else {
      setEditingJob(null);
      setJobForm({
        title: "", location: "", department: "", employment_type: "full_time",
        shift: "", pay_rate_min: "", pay_rate_max: "", pay_type: "hourly",
        description: "", requirements: "", positions_available: 1
      });
    }
    setJobDialogOpen(true);
  };

  const handleSaveJob = async () => {
    if (!jobForm.title || !jobForm.location || !jobForm.description) {
      toast.error("Please fill required fields");
      return;
    }

    setSavingJob(true);
    try {
      const payload = {
        ...jobForm,
        pay_rate_min: jobForm.pay_rate_min ? parseFloat(jobForm.pay_rate_min) : null,
        pay_rate_max: jobForm.pay_rate_max ? parseFloat(jobForm.pay_rate_max) : null,
        requirements: jobForm.requirements.split("\n").filter(r => r.trim())
      };

      if (editingJob) {
        await axios.put(`${API}/ats/jobs/${editingJob.job_id}`, payload);
        toast.success("Job updated");
      } else {
        await axios.post(`${API}/ats/jobs`, payload);
        toast.success("Job created");
      }

      setJobDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save job");
    } finally {
      setSavingJob(false);
    }
  };

  const handlePublishJob = async (jobId) => {
    try {
      await axios.post(`${API}/ats/jobs/${jobId}/publish`, null, {
        params: { platforms: ["internal"] }
      });
      toast.success("Job published");
      fetchData();
    } catch (error) {
      toast.error("Failed to publish job");
    }
  };

  const handleUpdateStage = async (applicantId, stage) => {
    try {
      await axios.post(`${API}/ats/applicants/${applicantId}/stage`, { stage });
      toast.success(`Moved to ${stage}`);
      fetchData();
      if (selectedApplicant?.applicant_id === applicantId) {
        const res = await axios.get(`${API}/ats/applicants/${applicantId}`);
        setSelectedApplicant(res.data);
      }
    } catch (error) {
      toast.error("Failed to update stage");
    }
  };

  const viewApplicant = async (applicantId) => {
    try {
      const res = await axios.get(`${API}/ats/applicants/${applicantId}`);
      setSelectedApplicant(res.data);
      setApplicantDialogOpen(true);
    } catch (error) {
      toast.error("Failed to load applicant");
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: "bg-gray-500",
      open: "bg-green-500",
      paused: "bg-yellow-500",
      closed: "bg-gray-600",
      filled: "bg-keystone"
    };
    return <Badge className={`${colors[status] || "bg-gray-500"} text-white`}>{status}</Badge>;
  };

  const getStageBadge = (stage) => {
    const colors = {
      new: "bg-blue-500",
      screening: "bg-yellow-500",
      interview: "bg-purple-500",
      offer: "bg-orange-500",
      hired: "bg-green-500",
      rejected: "bg-red-500"
    };
    return <Badge className={`${colors[stage] || "bg-gray-500"} text-white`}>{stage}</Badge>;
  };

  const filteredJobs = jobs.filter(job => {
    if (statusFilter !== "all" && job.status !== statusFilter) return false;
    if (searchTerm && !job.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-keystone" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-4 space-y-6 pb-24 lg:pb-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-serif text-3xl font-bold text-foundation">Recruiting</h1>
            <p className="text-muted-foreground">Applicant Tracking System</p>
          </div>
          <Button onClick={() => openJobDialog()} className="bg-keystone hover:bg-keystone/90">
            <Plus className="w-4 h-4 mr-2" />
            Post New Job
          </Button>
        </div>

        {/* Pipeline Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <Card className="bg-white border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">New</p>
                <p className="font-mono text-2xl font-bold text-blue-500">{stats.pipeline.new}</p>
              </CardContent>
            </Card>
            <Card className="bg-white border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">Screening</p>
                <p className="font-mono text-2xl font-bold text-yellow-500">{stats.pipeline.screening}</p>
              </CardContent>
            </Card>
            <Card className="bg-white border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">Interview</p>
                <p className="font-mono text-2xl font-bold text-purple-500">{stats.pipeline.interview}</p>
              </CardContent>
            </Card>
            <Card className="bg-white border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">Offer</p>
                <p className="font-mono text-2xl font-bold text-orange-500">{stats.pipeline.offer}</p>
              </CardContent>
            </Card>
            <Card className="bg-white border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">Hired</p>
                <p className="font-mono text-2xl font-bold text-green-500">{stats.pipeline.hired}</p>
              </CardContent>
            </Card>
            <Card className="bg-white border-0 shadow-sm border-t-2 border-t-keystone">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground uppercase">Conversion</p>
                <p className="font-mono text-2xl font-bold text-keystone">{stats.conversion_rate}%</p>
              </CardContent>
            </Card>
          </div>
        )}

        <Tabs defaultValue="jobs" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md bg-horizon">
            <TabsTrigger value="jobs" className="data-[state=active]:bg-keystone data-[state=active]:text-white">
              <Briefcase className="w-4 h-4 mr-2" />
              Jobs ({jobs.length})
            </TabsTrigger>
            <TabsTrigger value="applicants" className="data-[state=active]:bg-keystone data-[state=active]:text-white">
              <Users className="w-4 h-4 mr-2" />
              Applicants ({applicants.length})
            </TabsTrigger>
          </TabsList>

          {/* Jobs Tab */}
          <TabsContent value="jobs" className="mt-6 space-y-4">
            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 bg-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="filled">Filled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Jobs List */}
            <div className="space-y-3">
              {filteredJobs.map((job) => (
                <Card key={job.job_id} className="bg-white border-0 shadow-sm hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-foundation">{job.title}</h3>
                          {getStatusBadge(job.status)}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground flex-wrap">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {job.location}
                          </span>
                          {job.pay_rate_min && (
                            <span className="flex items-center gap-1">
                              <DollarSign className="w-3 h-3" />
                              ${job.pay_rate_min}{job.pay_rate_max ? `-$${job.pay_rate_max}` : ""}/{job.pay_type === "hourly" ? "hr" : "yr"}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {job.applicant_count || 0} applicants
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {job.new_applicants > 0 && (
                          <Badge className="bg-vertex text-white">{job.new_applicants} new</Badge>
                        )}
                        {job.status === "draft" && (
                          <Button size="sm" onClick={() => handlePublishJob(job.job_id)} className="bg-green-500">
                            <Send className="w-3 h-3 mr-1" />
                            Publish
                          </Button>
                        )}
                        <Button variant="outline" size="sm" onClick={() => openJobDialog(job)}>
                          <Edit2 className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {filteredJobs.length === 0 && (
                <Card className="bg-white border-0">
                  <CardContent className="py-12 text-center">
                    <Briefcase className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">No jobs found</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Applicants Tab */}
          <TabsContent value="applicants" className="mt-6 space-y-4">
            <div className="space-y-3">
              {applicants.map((app) => (
                <Card key={app.applicant_id} className="bg-white border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer" onClick={() => viewApplicant(app.applicant_id)}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-keystone/10 flex items-center justify-center">
                          <Users className="w-5 h-5 text-keystone" />
                        </div>
                        <div>
                          <p className="font-semibold text-foundation">{app.first_name} {app.last_name}</p>
                          <p className="text-sm text-muted-foreground">{app.job_title} • {app.job_location}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {app.rating && (
                          <div className="flex items-center gap-1 text-yellow-500">
                            <Star className="w-4 h-4 fill-current" />
                            <span className="text-sm">{app.rating}</span>
                          </div>
                        )}
                        {getStageBadge(app.stage)}
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {applicants.length === 0 && (
                <Card className="bg-white border-0">
                  <CardContent className="py-12 text-center">
                    <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">No applicants yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Job Dialog */}
        <Dialog open={jobDialogOpen} onOpenChange={setJobDialogOpen}>
          <DialogContent className="bg-white max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-serif text-xl">
                {editingJob ? "Edit Job Posting" : "Create Job Posting"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">Job Title *</label>
                  <Input
                    placeholder="e.g., Custodial Associate"
                    value={jobForm.title}
                    onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Location *</label>
                  <Input
                    placeholder="e.g., Memphis, TN"
                    value={jobForm.location}
                    onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })}
                    className="mt-1"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">Type</label>
                  <Select value={jobForm.employment_type} onValueChange={(v) => setJobForm({ ...jobForm, employment_type: v })}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full_time">Full Time</SelectItem>
                      <SelectItem value="part_time">Part Time</SelectItem>
                      <SelectItem value="contract">Contract</SelectItem>
                      <SelectItem value="temp">Temporary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Shift</label>
                  <Input
                    placeholder="e.g., Day, Night"
                    value={jobForm.shift}
                    onChange={(e) => setJobForm({ ...jobForm, shift: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Positions</label>
                  <Input
                    type="number"
                    min="1"
                    value={jobForm.positions_available}
                    onChange={(e) => setJobForm({ ...jobForm, positions_available: parseInt(e.target.value) || 1 })}
                    className="mt-1"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">Pay Min ($)</label>
                  <Input
                    type="number"
                    placeholder="15.00"
                    value={jobForm.pay_rate_min}
                    onChange={(e) => setJobForm({ ...jobForm, pay_rate_min: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Pay Max ($)</label>
                  <Input
                    type="number"
                    placeholder="20.00"
                    value={jobForm.pay_rate_max}
                    onChange={(e) => setJobForm({ ...jobForm, pay_rate_max: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Pay Type</label>
                  <Select value={jobForm.pay_type} onValueChange={(v) => setJobForm({ ...jobForm, pay_type: v })}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">Hourly</SelectItem>
                      <SelectItem value="salary">Salary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <label className="text-sm text-muted-foreground">Job Description *</label>
                <Textarea
                  placeholder="Describe the role, responsibilities, and work environment..."
                  value={jobForm.description}
                  onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                  className="mt-1 min-h-[100px]"
                />
              </div>
              
              <div>
                <label className="text-sm text-muted-foreground">Requirements (one per line)</label>
                <Textarea
                  placeholder="Must be able to lift 50 lbs&#10;Valid driver's license&#10;Able to work flexible hours"
                  value={jobForm.requirements}
                  onChange={(e) => setJobForm({ ...jobForm, requirements: e.target.value })}
                  className="mt-1 min-h-[80px]"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setJobDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleSaveJob} disabled={savingJob} className="bg-keystone">
                {savingJob && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                {editingJob ? "Update" : "Create"} Job
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Applicant Detail Dialog */}
        <Dialog open={applicantDialogOpen} onOpenChange={setApplicantDialogOpen}>
          <DialogContent className="bg-white max-w-2xl max-h-[90vh] overflow-y-auto">
            {selectedApplicant && (
              <>
                <DialogHeader>
                  <DialogTitle className="font-serif text-xl">
                    {selectedApplicant.applicant?.first_name} {selectedApplicant.applicant?.last_name}
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="flex items-center gap-2 flex-wrap">
                    {getStageBadge(selectedApplicant.applicant?.stage)}
                    <span className="text-muted-foreground">for</span>
                    <span className="font-medium">{selectedApplicant.job?.title}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 p-4 bg-horizon rounded">
                    <div>
                      <p className="text-xs text-muted-foreground">Email</p>
                      <p className="font-medium">{selectedApplicant.applicant?.email}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Phone</p>
                      <p className="font-medium">{selectedApplicant.applicant?.phone}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Source</p>
                      <p className="font-medium capitalize">{selectedApplicant.applicant?.source}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Applied</p>
                      <p className="font-medium">
                        {format(new Date(selectedApplicant.applicant?.created_at), "MMM d, yyyy")}
                      </p>
                    </div>
                  </div>
                  
                  {/* Stage Actions */}
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Move to Stage</p>
                    <div className="flex flex-wrap gap-2">
                      {["screening", "interview", "offer", "hired", "rejected"].map((stage) => (
                        <Button
                          key={stage}
                          size="sm"
                          variant={selectedApplicant.applicant?.stage === stage ? "default" : "outline"}
                          onClick={() => handleUpdateStage(selectedApplicant.applicant?.applicant_id, stage)}
                          className={selectedApplicant.applicant?.stage === stage ? "bg-keystone" : ""}
                        >
                          {stage === "hired" && <CheckCircle2 className="w-3 h-3 mr-1" />}
                          {stage === "rejected" && <XCircle className="w-3 h-3 mr-1" />}
                          {stage.charAt(0).toUpperCase() + stage.slice(1)}
                        </Button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Stage History */}
                  {selectedApplicant.applicant?.stage_history?.length > 0 && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">History</p>
                      <div className="space-y-2">
                        {selectedApplicant.applicant.stage_history.map((entry, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <Badge variant="outline">{entry.stage}</Badge>
                            <span className="text-muted-foreground">
                              {format(new Date(entry.timestamp), "MMM d, h:mm a")}
                            </span>
                            {entry.by_name && <span className="text-muted-foreground">by {entry.by_name}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default ATS;
