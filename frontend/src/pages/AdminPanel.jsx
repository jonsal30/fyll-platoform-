import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "../components/ui/dialog";
import {
  MapPin,
  Users,
  Settings,
  Plus,
  Edit2,
  Trash2,
  Loader2,
  CheckCircle2,
  FileSpreadsheet,
  ExternalLink,
  Building2,
  Globe,
} from "lucide-react";

const AdminPanel = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();

  const [sites, setSites] = useState([]);
  const [users, setUsers] = useState([]);
  const [sheetsStatus, setSheetsStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const [siteDialogOpen, setSiteDialogOpen] = useState(false);
  const [editingSite, setEditingSite] = useState(null);
  const [siteForm, setSiteForm] = useState({
    name: "",
    address: "",
    latitude: "",
    longitude: "",
    radius_meters: 200,
  });
  const [savingSite, setSavingSite] = useState(false);

  const [editingUser, setEditingUser] = useState(null);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [userForm, setUserForm] = useState({
    role: "",
    numeric_id: "",
    pin: "",
    assigned_sites: [],
  });
  const [savingUser, setSavingUser] = useState(false);

  useEffect(() => {
    fetchData();

    // Check if redirected from Sheets OAuth
    if (searchParams.get("sheets") === "connected") {
      toast.success("Google Sheets connected successfully!");
    }
  }, [searchParams]);

  const fetchData = async () => {
    try {
      const [sitesRes, usersRes, sheetsRes] = await Promise.all([
        axios.get(`${API}/sites`),
        axios.get(`${API}/users`),
        axios.get(`${API}/sheets/status`),
      ]);
      setSites(sitesRes.data);
      setUsers(usersRes.data);
      setSheetsStatus(sheetsRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Site Management
  const openSiteDialog = (site = null) => {
    if (site) {
      setEditingSite(site);
      setSiteForm({
        name: site.name,
        address: site.address,
        latitude: site.latitude.toString(),
        longitude: site.longitude.toString(),
        radius_meters: site.radius_meters,
      });
    } else {
      setEditingSite(null);
      setSiteForm({
        name: "",
        address: "",
        latitude: "",
        longitude: "",
        radius_meters: 200,
      });
    }
    setSiteDialogOpen(true);
  };

  const handleSaveSite = async () => {
    if (
      !siteForm.name ||
      !siteForm.address ||
      !siteForm.latitude ||
      !siteForm.longitude
    ) {
      toast.error("Please fill all required fields");
      return;
    }

    setSavingSite(true);
    try {
      const payload = {
        name: siteForm.name,
        address: siteForm.address,
        latitude: parseFloat(siteForm.latitude),
        longitude: parseFloat(siteForm.longitude),
        radius_meters: parseInt(siteForm.radius_meters),
      };

      if (editingSite) {
        await axios.put(`${API}/sites/${editingSite.site_id}`, payload);
        toast.success("Site updated");
      } else {
        await axios.post(`${API}/sites`, payload);
        toast.success("Site created");
      }

      setSiteDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save site");
    } finally {
      setSavingSite(false);
    }
  };

  const handleDeleteSite = async (siteId) => {
    if (!window.confirm("Are you sure you want to deactivate this site?"))
      return;

    try {
      await axios.delete(`${API}/sites/${siteId}`);
      toast.success("Site deactivated");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete site");
    }
  };

  // User Management
  const openUserDialog = (userData) => {
    setEditingUser(userData);
    setUserForm({
      role: userData.role || "employee",
      numeric_id: userData.numeric_id || "",
      pin: "",
      assigned_sites: userData.assigned_sites || [],
    });
    setUserDialogOpen(true);
  };

  const handleSaveUser = async () => {
    setSavingUser(true);
    try {
      await axios.put(`${API}/users/${editingUser.user_id}`, {
        role: userForm.role,
        numeric_id: userForm.numeric_id || null,
        pin: userForm.pin || null,
        assigned_sites: userForm.assigned_sites,
      });
      toast.success("User updated");
      setUserDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update user");
    } finally {
      setSavingUser(false);
    }
  };

  // Google Sheets
  const handleConnectSheets = async () => {
    try {
      const response = await axios.get(`${API}/oauth/sheets/login`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
          "Failed to initiate Google Sheets connection",
      );
    }
  };

  const getRoleBadge = (role) => {
    const variants = {
      admin: "default",
      manager: "secondary",
      employee: "outline",
    };
    return <Badge variant={variants[role] || "outline"}>{role}</Badge>;
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

  return (
    <Layout>
      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* Header */}
        <div>
          <h1 className="font-heading text-3xl font-bold">Admin Panel</h1>
          <p className="text-muted-foreground">
            Manage sites, users, and integrations
          </p>
        </div>

        <Tabs defaultValue="sites" className="w-full">
          <TabsList className="grid w-full grid-cols-3 max-w-lg bg-horizon">
            <TabsTrigger
              value="sites"
              className="flex items-center gap-2 data-[state=active]:bg-keystone data-[state=active]:text-white"
            >
              <MapPin className="w-4 h-4" />
              Sites
            </TabsTrigger>
            <TabsTrigger
              value="users"
              data-testid="users-tab"
              className="flex items-center gap-2 data-[state=active]:bg-keystone data-[state=active]:text-white"
            >
              <Users className="w-4 h-4" />
              Users
            </TabsTrigger>
            <TabsTrigger
              value="integrations"
              data-testid="integrations-tab"
              className="flex items-center gap-2 data-[state=active]:bg-keystone data-[state=active]:text-white"
            >
              <Settings className="w-4 h-4" />
              Integrations
            </TabsTrigger>
          </TabsList>

          {/* Sites Tab */}
          <TabsContent value="sites" className="mt-6 space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-muted-foreground">
                {sites.length} work sites configured
              </p>
              <Button
                onClick={() => openSiteDialog()}
                data-testid="add-site-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Site
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {sites.map((site) => (
                <Card key={site.site_id} className="bg-card border-border">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-sm bg-primary/10 flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-semibold">{site.name}</p>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {site.address}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openSiteDialog(site)}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteSite(site.site_id)}
                        >
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-mono flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {site.latitude.toFixed(4)}, {site.longitude.toFixed(4)}
                      </span>
                      <Badge variant="outline">{site.radius_meters}m</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Site Dialog */}
            <Dialog open={siteDialogOpen} onOpenChange={setSiteDialogOpen}>
              <DialogContent className="bg-card border-border">
                <DialogHeader>
                  <DialogTitle className="font-heading">
                    {editingSite ? "Edit Site" : "Add New Site"}
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Site Name
                    </label>
                    <Input
                      data-testid="site-name-input"
                      placeholder="e.g., Main Warehouse"
                      value={siteForm.name}
                      onChange={(e) =>
                        setSiteForm({ ...siteForm, name: e.target.value })
                      }
                      className="bg-background mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Address
                    </label>
                    <Input
                      data-testid="site-address-input"
                      placeholder="Full address"
                      value={siteForm.address}
                      onChange={(e) =>
                        setSiteForm({ ...siteForm, address: e.target.value })
                      }
                      className="bg-background mt-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-muted-foreground">
                        Latitude
                      </label>
                      <Input
                        data-testid="site-lat-input"
                        type="number"
                        step="any"
                        placeholder="e.g., 40.7128"
                        value={siteForm.latitude}
                        onChange={(e) =>
                          setSiteForm({ ...siteForm, latitude: e.target.value })
                        }
                        className="bg-background mt-1 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">
                        Longitude
                      </label>
                      <Input
                        data-testid="site-lng-input"
                        type="number"
                        step="any"
                        placeholder="e.g., -74.0060"
                        value={siteForm.longitude}
                        onChange={(e) =>
                          setSiteForm({
                            ...siteForm,
                            longitude: e.target.value,
                          })
                        }
                        className="bg-background mt-1 font-mono"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Geo-fence Radius (meters)
                    </label>
                    <Input
                      data-testid="site-radius-input"
                      type="number"
                      value={siteForm.radius_meters}
                      onChange={(e) =>
                        setSiteForm({
                          ...siteForm,
                          radius_meters: e.target.value,
                        })
                      }
                      className="bg-background mt-1 font-mono"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setSiteDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveSite}
                    disabled={savingSite}
                    data-testid="save-site-btn"
                  >
                    {savingSite && (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    )}
                    Save
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="mt-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-xl">
                  User Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table className="data-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Numeric ID</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Sites</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.user_id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                              {u.picture ? (
                                <img
                                  src={u.picture}
                                  alt=""
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <Users className="w-4 h-4 text-muted-foreground" />
                              )}
                            </div>
                            <span className="font-medium">{u.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {u.email}
                        </TableCell>
                        <TableCell className="font-mono">
                          {u.numeric_id || "-"}
                        </TableCell>
                        <TableCell>{getRoleBadge(u.role)}</TableCell>
                        <TableCell>
                          <span className="text-muted-foreground text-xs">
                            {u.assigned_sites?.length || 0} sites
                          </span>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openUserDialog(u)}
                            data-testid={`edit-user-${u.user_id}`}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* User Dialog */}
            <Dialog open={userDialogOpen} onOpenChange={setUserDialogOpen}>
              <DialogContent className="bg-card border-border">
                <DialogHeader>
                  <DialogTitle className="font-heading">
                    Edit User: {editingUser?.name}
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Role
                    </label>
                    <Select
                      value={userForm.role}
                      onValueChange={(v) =>
                        setUserForm({ ...userForm, role: v })
                      }
                    >
                      <SelectTrigger
                        className="bg-background mt-1"
                        data-testid="user-role-select"
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="employee">Employee</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Numeric ID (for quick login)
                    </label>
                    <Input
                      data-testid="user-numeric-id-input"
                      placeholder="e.g., 1234"
                      value={userForm.numeric_id}
                      onChange={(e) =>
                        setUserForm({ ...userForm, numeric_id: e.target.value })
                      }
                      className="bg-background mt-1 font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Set or reset private PIN
                    </label>
                    <Input
                      data-testid="user-pin-input"
                      type="password"
                      inputMode="numeric"
                      placeholder="4–12 digits; leave blank to keep current PIN"
                      value={userForm.pin}
                      onChange={(e) =>
                        setUserForm({
                          ...userForm,
                          pin: e.target.value.replace(/\D/g, "").slice(0, 12),
                        })
                      }
                      className="bg-background mt-1 font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Share the initial PIN privately and ask the employee not
                      to reuse a banking PIN.
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Assigned Sites
                    </label>
                    <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
                      {sites.map((site) => (
                        <label
                          key={site.site_id}
                          className="flex items-center gap-2 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={userForm.assigned_sites.includes(
                              site.site_id,
                            )}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setUserForm({
                                  ...userForm,
                                  assigned_sites: [
                                    ...userForm.assigned_sites,
                                    site.site_id,
                                  ],
                                });
                              } else {
                                setUserForm({
                                  ...userForm,
                                  assigned_sites:
                                    userForm.assigned_sites.filter(
                                      (s) => s !== site.site_id,
                                    ),
                                });
                              }
                            }}
                            className="rounded border-border"
                          />
                          <span className="text-sm">{site.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setUserDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveUser}
                    disabled={savingUser}
                    data-testid="save-user-btn"
                  >
                    {savingUser && (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    )}
                    Save
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </TabsContent>

          {/* Integrations Tab */}
          <TabsContent value="integrations" className="mt-6 space-y-4">
            {/* Google Sheets */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-xl flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-success" />
                  Google Sheets Integration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Sync approved timesheets directly to Google Sheets for
                      payroll processing.
                    </p>
                    {sheetsStatus?.connected && (
                      <div className="mt-2 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-success" />
                        <span className="text-sm text-success">Connected</span>
                        {sheetsStatus.spreadsheet_id && (
                          <a
                            href={`https://docs.google.com/spreadsheets/d/${sheetsStatus.spreadsheet_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-secondary flex items-center gap-1 hover:underline"
                          >
                            Open Sheet <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    )}
                  </div>

                  {sheetsStatus?.connected ? (
                    <Badge
                      variant="outline"
                      className="text-success border-success"
                    >
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Active
                    </Badge>
                  ) : (
                    <Button
                      onClick={handleConnectSheets}
                      data-testid="connect-sheets-btn"
                    >
                      <FileSpreadsheet className="w-4 h-4 mr-2" />
                      Connect Google Sheets
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* CSV Export Info */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-xl flex items-center gap-2">
                  <Settings className="w-5 h-5 text-secondary" />
                  CSV Export
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  CSV export is always available as a backup. Employees and
                  managers can export their timesheets directly from the
                  Timesheet page.
                </p>
                <Badge variant="outline" className="mt-2">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Always Available
                </Badge>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default AdminPanel;
