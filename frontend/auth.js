// Shared Supabase auth helpers — included by all pages via <script src="/auth.js">
let _supabase = null;

async function initSupabase() {
    // Only create the client once — reuse the same instance across the page
    if (_supabase) return _supabase;
    // Fetch Supabase credentials from our FastAPI /config endpoint
    // (keeps keys out of committed code)
    const res = await fetch("/config");
    const { supabaseUrl, supabaseAnonKey } = await res.json();
    _supabase = window.supabase.createClient(supabaseUrl, supabaseAnonKey);
    return _supabase;
}

// Returns the existing client, or initializes it if this is the first call
async function getSupabase() {
    return _supabase || initSupabase();
}

// Use on protected pages (e.g. dashboard).
// If no active session, sends user to /login. Otherwise returns the user object.
async function requireAuth() {
    const sb = await getSupabase();
    const { data: { user } } = await sb.auth.getUser();
    if (!user) {
        window.location.href = "/login";
        return null;
    }
    return user;
}

// Use on public pages (e.g. landing, login).
// If user is already logged in, skip the page and send them to /dashboard.
async function redirectIfLoggedIn() {
    const sb = await getSupabase();
    const { data: { user } } = await sb.auth.getUser();
    if (user) window.location.href = "/dashboard";
}

async function logout() {
    const sb = await getSupabase();
    await sb.auth.signOut(); // clears the session token stored in the browser
    window.location.href = "/";
}
