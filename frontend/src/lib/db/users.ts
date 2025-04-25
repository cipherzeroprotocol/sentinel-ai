import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { hash } from 'bcryptjs';
import { User, ApiToken, UserRole, UserPreferences } from '@/types';

// In a real app, this would be a database connection
// For simplicity, we're using a JSON file in development
const DB_PATH = process.env.USER_DB_PATH || path.join(process.cwd(), 'data', 'users.json');

// Ensure the directory exists
const dbDir = path.dirname(DB_PATH);
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize DB if it doesn't exist
if (!fs.existsSync(DB_PATH)) {
  fs.writeFileSync(DB_PATH, JSON.stringify({ users: [] }));
}

// Helper to read the database
function readDB(): { users: (User & { password: string })[] } {
  try {
    const data = fs.readFileSync(DB_PATH, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading user database:', error);
    return { users: [] };
  }
}

// Helper to write to the database
function writeDB(data: { users: (User & { password: string })[] }) {
  try {
    fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('Error writing to user database:', error);
    throw error;
  }
}

// Get user by email
export async function getUserByEmail(email: string): Promise<(User & { password: string }) | null> {
  const db = readDB();
  const user = db.users.find(u => u.email.toLowerCase() === email.toLowerCase());
  return user || null;
}

// Get user by ID
export async function getUserById(id: string): Promise<User | null> {
  const db = readDB();
  const user = db.users.find(u => u.id === id);
  
  if (!user) return null;
  
  // Remove password before returning
  const { password, ...userWithoutPassword } = user;
  return userWithoutPassword;
}

// Create a new user
export async function createUser(userData: { 
  email: string; 
  password: string; 
  name?: string; 
  role?: UserRole;
}): Promise<User> {
  const db = readDB();
  
  // Check if user already exists
  if (db.users.some(u => u.email.toLowerCase() === userData.email.toLowerCase())) {
    throw new Error('User with this email already exists');
  }
  
  // Hash the password
  const hashedPassword = await hash(userData.password, 12);
  
  const now = new Date().toISOString();
  
  // Explicitly type newUser to match the expected structure including nested preferences
  const newUser: User & { password: string } = {
    id: uuidv4(),
    email: userData.email,
    password: hashedPassword,
    name: userData.name || userData.email.split('@')[0],
    role: userData.role || UserRole.USER,
    apiTokens: [], // Assuming User type expects ApiToken[]
    preferences: {
      theme: 'system', // Ensure 'system' is a valid literal for UserPreferences['theme']
      notifications: { email: true, inApp: true },
      visualizations: { showRiskMetrics: true }
      // Add other default preferences if defined in UserPreferences type
    },
    createdAt: now,
    updatedAt: now,
  };
  
  db.users.push(newUser);
  writeDB(db);
  
  // Return user without password
  const { password, ...userWithoutPassword } = newUser;
  return userWithoutPassword;
}

// Update user
export async function updateUser(id: string, updates: Partial<User>): Promise<User | null> {
  const db = readDB();
  const userIndex = db.users.findIndex(u => u.id === id);
  
  if (userIndex === -1) return null;
  
  // Apply updates
  db.users[userIndex] = {
    ...db.users[userIndex],
    ...updates,
    updatedAt: new Date().toISOString()
  };
  
  writeDB(db);
  
  // Return updated user without password
  const { password, ...userWithoutPassword } = db.users[userIndex];
  return userWithoutPassword;
}

// Update user preferences
export async function updateUserPreferences(
  userId: string, 
  preferences: Partial<UserPreferences>
): Promise<User | null> {
  const db = readDB();
  const userIndex = db.users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) return null;
  
  // Update preferences
  db.users[userIndex].preferences = {
    ...db.users[userIndex].preferences || {},
    ...preferences
  };
  
  db.users[userIndex].updatedAt = new Date().toISOString();
  
  writeDB(db);
  
  // Return updated user without password
  const { password, ...userWithoutPassword } = db.users[userIndex];
  return userWithoutPassword;
}

// Create API token for user
export async function createApiToken(
  userId: string, 
  tokenName: string,
  expiresInDays?: number
): Promise<ApiToken | null> {
  const db = readDB();
  const userIndex = db.users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) return null;
  
  const now = new Date();
  const expiresAt = expiresInDays 
    ? new Date(now.getTime() + expiresInDays * 24 * 60 * 60 * 1000).toISOString() 
    : undefined;
  
  const newToken: ApiToken = {
    id: uuidv4(),
    name: tokenName,
    token: `sentinel_${uuidv4().replace(/-/g, '')}`,
    createdAt: now.toISOString(),
    expiresAt
  };
  
  if (!db.users[userIndex].apiTokens) {
    db.users[userIndex].apiTokens = [];
  }
  
  db.users[userIndex].apiTokens.push(newToken);
  db.users[userIndex].updatedAt = now.toISOString();
  
  writeDB(db);
  
  return newToken;
}

// Delete API token
export async function deleteApiToken(userId: string, tokenId: string): Promise<boolean> {
  const db = readDB();
  const userIndex = db.users.findIndex(u => u.id === userId);
  
  if (userIndex === -1 || !db.users[userIndex].apiTokens) return false;
  
  const tokenIndex = db.users[userIndex].apiTokens.findIndex(t => t.id === tokenId);
  
  if (tokenIndex === -1) return false;
  
  db.users[userIndex].apiTokens.splice(tokenIndex, 1);
  db.users[userIndex].updatedAt = new Date().toISOString();
  
  writeDB(db);
  
  return true;
}

// Initialize the database with an admin user if it's empty
export async function initializeUsers() {
  const db = readDB();
  
  try {
    // More robust check: look for admin user specifically to avoid recreating users
    const adminExists = db.users.some(u => u.email.toLowerCase() === 'admin@sentinel.ai');
    
    if (!adminExists) { // Only create users if admin doesn't exist
      console.log("No admin user found, creating initial users...");
      
      // Create the users as before
      await createUser({
        email: "admin@sentinel.ai",
        password: "Sentinel@123",
        name: "Admin",
        role: UserRole.ADMIN
      });
      
      await createUser({
        email: 'analyst@sentinel.ai',
        password: 'Analysis@123',
        name: 'Security Analyst',
        role: UserRole.ANALYST
      });
      
      await createUser({
        email: 'user@sentinel.ai',
        password: 'User@123',
        name: 'Regular User',
        role: UserRole.USER
      });
      
      console.log("Created initial users");
    } else {
      console.log("Initial users already exist, skipping creation");
    }
  } catch (error) {
    console.error("Error during user initialization:", error);
    // Don't throw - allow app to continue even if initialization fails
  }
}

// Initialize users when imported in development
if (process.env.NODE_ENV === 'development') {
  console.log("Development mode detected, initializing users...");
  initializeUsers()
    .then(() => console.log("Users initialization complete"))
    .catch(error => console.error("Failed to initialize users:", error));
}
