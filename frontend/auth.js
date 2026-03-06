// Shared Supabase auth helpers — included by all pages
let _supabase = null;

async function initSupabase() {
    if (_supabase) return _supabase;
    const res = await fetch("/config");
    const { supabaseUrl, supabaseAnonKey } = await res.json();
    _supabase = window.supabase.createClient(supabaseUrl, supabaseAnonKey);
    return _supabase;
}

async function getSupabase() {
    return _supabase || initSupabase();
}

// Redirect to /login if not authenticated, returns user if authenticated
async function requireAuth() {
    const sb = await getSupabase();
    const { data: { user } } = await sb.auth.getUser();
    if (!user) {
        window.location.href = "/login";
        return null;
    }
    return user;
}

// Redirect to /dashboard if already logged in
async function redirectIfLoggedIn() {
    const sb = await getSupabase();
    const { data: { user } } = await sb.auth.getUser();
    if (user) window.location.href = "/dashboard";
}

async function logout() {
    const sb = await getSupabase();
    await sb.auth.signOut();
    window.location.href = "/";
}
