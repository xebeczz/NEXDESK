import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  User,
  Key,
  Monitor,
  Bell,
  Shield,
  UserPlus,
  Mail,
  Smartphone,
  Lock,
  Eye,
  EyeOff,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle,
  QrCode,
  Copy,
  AlertTriangle,
  Moon,
  FileText,
  MessageSquare,
  Calendar,
  Download,
  Trash2,
  AtSign,
} from "lucide-react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { settingsApi, type NotificationPreferences } from "@/api/endpoints";
import { useAuth } from "@/providers/auth";
import { cn, extractErrorMessage } from "@/lib/utils";

const TABS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "password", label: "Change Password", icon: Key },
  { id: "appearance", label: "Appearance", icon: Monitor },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "account", label: "Account", icon: UserPlus },
  { id: "security", label: "Security", icon: Shield },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SettingsPage() {
  const { user, setUser } = useAuth();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get("tab") as TabId) || "profile";
  const [activeTab, setActiveTab] = useState<TabId>(initialTab);
  const handleTabChange = (value: string) => {
    setActiveTab(value as TabId);
  };
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [twoFAModalOpen, setTwoFAModalOpen] = useState(false);
  const [twoFASecret, setTwoFASecret] = useState("");
  const [twoFAQRCode, setTwoFAQRCode] = useState("");
  const [twoFAVerifying, setTwoFAVerifying] = useState(false);

  // Fetch settings
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: settingsApi.getSettings,
  });

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || "",
    department: user?.department || "",
    username: user?.username || "",
    email: user?.email || "",
  });

  // Password form state
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  // Notification preferences state
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences>({
    email_notifications: true,
    push_notifications: true,
    ticket_updates: true,
    ticket_assignments: true,
    mentions: true,
    comments: true,
    weekly_digest: false,
  });

  // Initialize form data from settings
  useEffect(() => {
    if (settings) {
      setProfileForm({
        full_name: settings.user.full_name,
        department: settings.user.department || "",
        username: settings.user.username,
        email: settings.user.email,
      });

      setNotifPrefs(settings.notification_preferences);
    }
  }, [settings]);

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: (data) => {
      setUser(data);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Profile updated successfully");
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Failed to update profile"));
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      settingsApi.changePassword(current_password, new_password),
    onSuccess: () => {
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      toast.success("Password updated successfully");
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Failed to change password"));
    },
  });

  // Update notifications mutation
  const updateNotificationsMutation = useMutation({
    mutationFn: (data: NotificationPreferences) => settingsApi.updateNotifications(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Notification preferences updated");
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Failed to update notification preferences"));
    },
  });

  // Enable 2FA
  const enable2FAMutation = useMutation({
    mutationFn: settingsApi.enable2FA,
    onSuccess: (data) => {
      setTwoFASecret(data.secret);
      setTwoFAQRCode(data.qr_code);
      setTwoFAModalOpen(true);
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Failed to enable 2FA"));
    },
  });

  // Verify 2FA
  const verify2FAMutation = useMutation({
    mutationFn: (code: string) => settingsApi.verify2FA(code),
    onSuccess: () => {
      setTwoFAModalOpen(false);
      setTwoFAVerifying(false);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Two-factor authentication enabled successfully");
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Invalid code"));
      setTwoFAVerifying(false);
    },
  });

  // Disable 2FA
  const disable2FAMutation = useMutation({
    mutationFn: (code: string) => settingsApi.disable2FA(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Two-factor authentication disabled");
    },
    onError: (error: any) => {
      toast.error(extractErrorMessage(error, "Invalid code"));
    },
  });

  // Handle profile form submit
  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(profileForm);
  };

  // Handle password form submit
  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("New passwords do not match");
      return;
    }
    if (passwordForm.new_password.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }
    changePasswordMutation.mutate({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
  };

  // Handle notification preferences change
  const handleNotificationChange = (key: keyof NotificationPreferences, value: boolean) => {
    const newPrefs = { ...notifPrefs, [key]: value };
    setNotifPrefs(newPrefs);
    updateNotificationsMutation.mutate(newPrefs);
  };

   // Handle 2FA enable
  const handleEnable2FA = () => {
    enable2FAMutation.mutate();
  };

  // Handle 2FA verify
  const handleVerify2FA = (code: string) => {
    setTwoFAVerifying(true);
    verify2FAMutation.mutate(code);
  };

  // Handle 2FA disable
  const handleDisable2FA = (code: string) => {
    disable2FAMutation.mutate(code);
  };

  // Copy 2FA secret to clipboard
  const copySecret = () => {
    navigator.clipboard.writeText(twoFASecret);
    toast.success("Secret copied to clipboard");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">Failed to load settings</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account settings, preferences, and security.
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          {TABS.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information. This will be visible to other users.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileSubmit} className="space-y-6 max-w-2xl">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={profileForm.full_name}
                      onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      value={profileForm.username}
                      onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Input
                      id="department"
                      value={profileForm.department}
                      onChange={(e) => setProfileForm({ ...profileForm, department: e.target.value })}
                      placeholder="Optional"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={updateProfileMutation.isPending}>
                    {updateProfileMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Current User Info */}
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>Read-only information about your account.</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <dt className="text-sm text-muted-foreground">User ID</dt>
                  <dd className="font-mono text-sm">{user?.id}</dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm text-muted-foreground">Role</dt>
                  <dd className="capitalize">{user?.role}</dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm text-muted-foreground">Status</dt>
                  <dd className={cn("capitalize", user?.is_active ? "text-green-600" : "text-red-600")}>
                    {user?.is_active ? "Active" : "Inactive"}
                  </dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm text-muted-foreground">Member Since</dt>
                  <dd className="text-sm">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Unknown"}
                  </dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm text-muted-foreground">Last Login</dt>
                  <dd className="text-sm">
                    {user?.last_login_at
                      ? new Date(user.last_login_at).toLocaleString()
                      : "Never"}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Password Tab */}
        <TabsContent value="password" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>
                Update your password. Make sure to use a strong, unique password.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordSubmit} className="space-y-6 max-w-xl">
                <div className="space-y-2">
                  <Label htmlFor="current_password">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="current_password"
                      type={showCurrentPassword ? "text" : "password"}
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-[34px] h-8 w-8"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    >
                      {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new_password">New Password</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={showNewPassword ? "text" : "password"}
                      value={passwordForm.new_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                      required
                      minLength={8}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-[34px] h-8 w-8"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirm_password"
                      type={showConfirmPassword ? "text" : "password"}
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-[34px] h-8 w-8"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={changePasswordMutation.isPending}>
                    {changePasswordMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <Key className="mr-2 h-4 w-4" />
                        Update Password
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Password Strength Tips */}
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Password Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Use at least 12 characters</li>
                <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Mix uppercase, lowercase, numbers, and symbols</li>
                <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Avoid common words and personal information</li>
                <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Use a unique password for each service</li>
                <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Consider using a password manager</li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                The application uses a dark theme for optimal contrast and reduced eye strain.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between p-4 border rounded-lg bg-primary/5">
                <div className="flex items-center gap-3">
                  <Moon className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Dark Theme</p>
                    <p className="text-sm text-muted-foreground">Currently using dark mode for optimal viewing</p>
                  </div>
                </div>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                  Active
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Preview Card */}
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle>Preview</CardTitle>
              <CardDescription>See how your current theme looks.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-lg border bg-background">
                <div className="flex items-center gap-4 mb-4">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Preview Card</p>
                    <p className="text-sm text-muted-foreground">This is how cards will appear</p>
                  </div>
                </div>
                <Button variant="outline" className="w-full">Sample Button</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Control which notifications you receive and how they're delivered.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Delivery Methods */}
              <div>
                <h3 className="font-medium mb-4">Delivery Methods</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Email Notifications</p>
                        <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                      </div>
                    </div>
                    <Switch
                      checked={notifPrefs.email_notifications}
                      onCheckedChange={(checked) => handleNotificationChange("email_notifications", checked)}
                      disabled={updateNotificationsMutation.isPending}
                    />
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Smartphone className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Push Notifications</p>
                        <p className="text-sm text-muted-foreground">Receive browser push notifications</p>
                      </div>
                    </div>
                    <Switch
                      checked={notifPrefs.push_notifications}
                      onCheckedChange={(checked) => handleNotificationChange("push_notifications", checked)}
                      disabled={updateNotificationsMutation.isPending}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notification Types */}
              <div>
                <h3 className="font-medium mb-4">Notification Types</h3>
                <div className="space-y-4">
                  {[
                    { key: "ticket_updates" as const, label: "Ticket Updates", description: "When tickets you created or are assigned to are updated", icon: <FileText className="h-5 w-5 text-muted-foreground" /> },
                    { key: "ticket_assignments" as const, label: "Ticket Assignments", description: "When a ticket is assigned to you", icon: <UserPlus className="h-5 w-5 text-muted-foreground" /> },
                    { key: "mentions" as const, label: "Mentions", description: "When you're mentioned in a comment", icon: <AtSign className="h-5 w-5 text-muted-foreground" /> },
                    { key: "comments" as const, label: "Comments", description: "When someone comments on your tickets", icon: <MessageSquare className="h-5 w-5 text-muted-foreground" /> },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {item.icon}
                        <div>
                          <p className="font-medium">{item.label}</p>
                          <p className="text-sm text-muted-foreground">{item.description}</p>
                        </div>
                      </div>
                      <Switch
                        checked={notifPrefs[item.key]}
                        onCheckedChange={(checked) => handleNotificationChange(item.key, checked)}
                        disabled={updateNotificationsMutation.isPending}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Digest */}
              <div>
                <h3 className="font-medium mb-4">Digest</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Weekly Digest</p>
                        <p className="text-sm text-muted-foreground">Receive a weekly summary of activity</p>
                      </div>
                    </div>
                    <Switch
                      checked={notifPrefs.weekly_digest}
                      onCheckedChange={(checked) => handleNotificationChange("weekly_digest", checked)}
                      disabled={updateNotificationsMutation.isPending}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Account Tab */}
        <TabsContent value="account" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Settings</CardTitle>
              <CardDescription>
                Manage your account and data preferences.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Data Export</p>
                    <p className="text-sm text-muted-foreground">Download a copy of your data</p>
                  </div>
                  <Button variant="outline" disabled>
                    <Download className="mr-2 h-4 w-4" />
                    Export Data
                  </Button>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Delete Account</p>
                    <p className="text-sm text-muted-foreground">Permanently delete your account and all data</p>
                  </div>
                  <Button variant="destructive" className="bg-destructive/10 text-destructive hover:bg-destructive/20">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-dashed border-destructive/20 bg-destructive/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5" />
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Once you delete your account, there is no going back. Please be certain.
                If you're sure you want to delete your account, click the button below.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          {/* Two-Factor Authentication */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Two-Factor Authentication (2FA)
              </CardTitle>
              <CardDescription>
                Add an extra layer of security to your account using an authenticator app.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!settings?.security_settings.two_factor_enabled ? (
                <div className="text-center py-8">
                  <Shield className="h-16 w-16 text-muted-foreground/50 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">Two-factor authentication is disabled</h3>
                  <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                    Enable 2FA to add an extra layer of security to your account. You'll need to enter a code
                    from your authenticator app each time you sign in.
                  </p>
                  <Button onClick={handleEnable2FA} disabled={enable2FAMutation.isPending}>
                    {enable2FAMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Setting up...
                      </>
                    ) : (
                      <>
                        <QrCode className="mr-2 h-4 w-4" />
                        Enable 2FA
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-green-50 border-green-200">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium text-green-800">Two-factor authentication is enabled</p>
                        <p className="text-sm text-green-700">Your account is protected with an authenticator app</p>
                      </div>
                    </div>
                    <Button variant="outline" onClick={() => setTwoFAModalOpen(true)}>
                      <QrCode className="mr-2 h-4 w-4" />
                      View Setup
                    </Button>
                  </div>
                  <Button variant="destructive" onClick={() => {
                    const code = prompt("Enter your 2FA code to disable:");
                    if (code) handleDisable2FA(code);
                  }}>
                    <Lock className="mr-2 h-4 w-4" />
                    Disable 2FA
                  </Button>
                </div>
              )}

              {/* Last Password Change */}
              {settings?.security_settings.last_password_change && (
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    Last password change:{" "}
                    <span className="font-medium">
                      {new Date(settings.security_settings.last_password_change).toLocaleString()}
                    </span>
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Sessions */}
          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
              <CardDescription>Manage your active login sessions.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg bg-primary/5">
                  <div className="flex items-center gap-3">
                    <Monitor className="h-5 w-5 text-primary" />
                    <div>
                      <p className="font-medium">Current Session</p>
                      <p className="text-sm text-muted-foreground">This device • Active now</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">Current</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Session management for other devices will be available in a future update.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 2FA Modal */}
      {twoFAModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {settings?.security_settings.two_factor_enabled ? "2FA Setup Details" : "Set Up Two-Factor Authentication"}
              </CardTitle>
              <CardDescription>
                {settings?.security_settings.two_factor_enabled
                  ? "Your 2FA is already enabled. Here are your setup details."
                  : "Scan the QR code with your authenticator app, then enter the code to verify."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!settings?.security_settings.two_factor_enabled && (
                <>
                  <div className="text-center">
                    <img
                      src={twoFAQRCode}
                      alt="2FA QR Code"
                      className="mx-auto border rounded-lg max-w-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Secret Key (Manual Entry)</Label>
                    <div className="flex gap-2">
                      <Input
                        value={twoFASecret}
                        readOnly
                        className="flex-1 font-mono text-sm"
                      />
                      <Button variant="outline" onClick={copySecret}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Save this secret key in a safe place. It can be used to recover access if you lose your device.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="2fa-code">Enter 6-digit code from authenticator app</Label>
                    <Input
                      id="2fa-code"
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      autoComplete="one-time-code"
                      onKeyDown={(e) => e.key === "Enter" && twoFASecret && handleVerify2FA(e.currentTarget.value)}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setTwoFAModalOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={() => {
                        const code = (document.getElementById("2fa-code") as HTMLInputElement)?.value;
                        if (code) handleVerify2FA(code);
                      }}
                      disabled={twoFAVerifying}
                    >
                      {twoFAVerifying ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        "Verify & Enable"
                      )}
                    </Button>
                  </div>
                </>
              )}
              {settings?.security_settings.two_factor_enabled && (
                <div className="space-y-4">
                  <div className="text-center">
                    <img
                      src={twoFAQRCode}
                      alt="2FA QR Code"
                      className="mx-auto border rounded-lg max-w-xs"
                    />
                  </div>
                  <div>
                    <Label>Secret Key</Label>
                    <div className="flex gap-2">
                      <Input
                        value={twoFASecret}
                        readOnly
                        className="flex-1 font-mono text-sm"
                      />
                      <Button variant="outline" onClick={copySecret}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <Button variant="outline" onClick={() => setTwoFAModalOpen(false)} className="w-full">
                    Close
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

