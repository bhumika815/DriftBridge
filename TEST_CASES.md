# 🧪 DriftBridge Testing Document

## Test Cases Based on Project Synopsis

---

## Module 1: User Authentication Module ✅

### Test Case 1.1: User Registration
**Steps:**
1. Go to registration page
2. Enter username, email, password
3. Click Register

**Expected Result:**
- User account created
- Redirected to login page
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 1.2: User Login
**Steps:**
1. Go to login page
2. Enter valid credentials
3. Click Login

**Expected Result:**
- User logged in successfully
- Redirected to dashboard
- Navigation menu visible

**Status:** ⏳ To Test

---

### Test Case 1.3: User Logout
**Steps:**
1. Click Logout in navigation
2. Confirm logout

**Expected Result:**
- User logged out
- Redirected to landing page
- Session cleared

**Status:** ⏳ To Test

---

## Module 2: User Profile Module ✅

### Test Case 2.1: View Profile
**Steps:**
1. Click "Profile" in navigation
2. View profile information

**Expected Result:**
- Profile page displays
- Shows username, email, bio, interests
- Shows reputation points and trust level

**Status:** ⏳ To Test

---

### Test Case 2.2: Edit Profile
**Steps:**
1. Go to Profile page
2. Edit bio and interests
3. Select preferred language
4. Click Save

**Expected Result:**
- Profile updated successfully
- Changes saved to database
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 2.3: Language Preference
**Steps:**
1. Go to Profile
2. Select a different language (e.g., Hindi)
3. Save profile

**Expected Result:**
- Language preference saved
- Future messages will be translated to selected language

**Status:** ⏳ To Test

---

## Module 3: Digital Bottle Module ✅

### Test Case 3.1: Throw Bottle
**Steps:**
1. Click "Throw Bottle" in navigation
2. Write a message
3. Click "Throw Bottle"

**Expected Result:**
- Bottle created and thrown
- +5 reputation points awarded
- Success message shown
- Redirected to throw bottle page

**Status:** ⏳ To Test

---

### Test Case 3.2: Throw Bottle with Inappropriate Content
**Steps:**
1. Go to Throw Bottle page
2. Write inappropriate/offensive message
3. Click "Throw Bottle"

**Expected Result:**
- AI detects inappropriate content
- Bottle NOT created
- Error message shown
- Content flagged

**Status:** ⏳ To Test

---

### Test Case 3.3: View Bottle Pool
**Steps:**
1. Click "Bottle Pool" in navigation
2. View available bottles

**Expected Result:**
- Display list of available bottles
- Shows bottle messages
- Shows sender username
- Shows "Keep" button

**Status:** ⏳ To Test

---

### Test Case 3.4: Keep a Bottle
**Steps:**
1. Go to Bottle Pool
2. Click "Keep" on a bottle

**Expected Result:**
- Bottle status changed to "claimed"
- Conversation created automatically
- +10 reputation points awarded
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 3.5: View Connections
**Steps:**
1. Click "Connections" in navigation
2. View connections list

**Expected Result:**
- Shows bottles you sent that were kept
- Shows bottles you kept
- Each connection has "Chat" button

**Status:** ⏳ To Test

---

## Module 4: Real-Time Chat Module ✅

### Test Case 4.1: Start Chat from Connections
**Steps:**
1. Go to Connections page
2. Click "Chat with [username]" button

**Expected Result:**
- Opens chat page
- Shows conversation history (if any)
- Chat input box visible

**Status:** ⏳ To Test

---

### Test Case 4.2: Send Message
**Steps:**
1. Open a chat
2. Type a message
3. Press Send or Enter

**Expected Result:**
- Message sent in real-time
- Message appears in chat window
- +2 reputation points awarded
- Message saved to database

**Status:** ⏳ To Test

---

### Test Case 4.3: Send Message with Inappropriate Content
**Steps:**
1. Open a chat
2. Type inappropriate message
3. Press Send

**Expected Result:**
- AI blocks the message
- Alert shown: "Message contains inappropriate content"
- Message NOT sent

**Status:** ⏳ To Test

---

### Test Case 4.4: Real-Time Message Delivery
**Steps:**
1. User A sends message to User B
2. User B has chat window open

**Expected Result:**
- Message appears instantly for User B
- No page refresh needed
- WebSocket connection working

**Status:** ⏳ To Test (needs 2 browsers)

---

### Test Case 4.5: AI Translation (Same Language)
**Steps:**
1. User A (English) sends "Hello" to User B (English)

**Expected Result:**
- Message appears as "Hello"
- No translation indicator
- Message in original language

**Status:** ⏳ To Test

---

### Test Case 4.6: AI Translation (Different Languages)
**Steps:**
1. User A sets language to English
2. User B sets language to Hindi
3. User A sends "How are you?"

**Expected Result:**
- User A sees: "How are you?"
- User B sees: "आप कैसे हैं?" (translated)
- Translation indicator shows "🌐 Translated"

**Status:** ⏳ To Test (needs 2 accounts with different languages)

---

### Test Case 4.7: View Conversations List
**Steps:**
1. Click "Chats" in navigation

**Expected Result:**
- Shows list of all conversations
- Shows connection name
- Shows connection date
- Click to open chat

**Status:** ⏳ To Test

---

## Module 5: Personal Journal Module ✅

### Test Case 5.1: Create Private Journal
**Steps:**
1. Click "Journals" in navigation
2. Click "New Journal"
3. Enter title and content
4. Select "Private" privacy
5. Add mood and tags (optional)
6. Click "Create Journal"

**Expected Result:**
- Journal created
- +15 reputation points awarded
- Visible only to you
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 5.2: Create Journal with Inappropriate Content
**Steps:**
1. Go to Create Journal
2. Write inappropriate content
3. Click "Create Journal"

**Expected Result:**
- AI blocks journal creation
- Error message shown
- Journal NOT created

**Status:** ⏳ To Test

---

### Test Case 5.3: View My Journals
**Steps:**
1. Click "Journals" in navigation
2. View journals list

**Expected Result:**
- Shows all your journals
- Displays title, excerpt, date
- Shows privacy badge
- Shows mood (if added)

**Status:** ⏳ To Test

---

### Test Case 5.4: Edit Journal
**Steps:**
1. Go to My Journals
2. Click "Edit" on a journal
3. Modify content
4. Click "Save Changes"

**Expected Result:**
- Journal updated
- Updated timestamp shown
- Changes saved to database

**Status:** ⏳ To Test

---

### Test Case 5.5: Delete Journal
**Steps:**
1. Go to My Journals
2. Click "Delete" on a journal
3. Confirm deletion

**Expected Result:**
- Journal deleted from database
- Removed from list
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 5.6: View Journal (Full View)
**Steps:**
1. Go to My Journals
2. Click "View" on a journal

**Expected Result:**
- Full journal content displayed
- Shows title, content, mood, tags
- Shows privacy setting
- Shows created/updated dates

**Status:** ⏳ To Test

---

### Test Case 5.7: Discover Public Journals
**Steps:**
1. Go to Journals → Discover tab

**Expected Result:**
- Shows public journals from other users
- Displays author name
- Shows excerpt
- Click to read full journal

**Status:** ⏳ To Test (needs another account with public journal)

---

### Test Case 5.8: View Connections' Journals
**Steps:**
1. Go to Journals → Connections tab

**Expected Result:**
- Shows journals from connections
- Shows journals marked as "Connections" or "Public"
- Displays author name

**Status:** ⏳ To Test (needs connection with journals)

---

### Test Case 5.9: Privacy Settings Test
**Steps:**
1. Create 3 journals: Private, Connections, Public
2. Login as another user (not connected)
3. Check Discover page

**Expected Result:**
- Only PUBLIC journal visible
- Private and Connections journals NOT visible

**Status:** ⏳ To Test (needs 2 accounts)

---

## Module 6: Story Module ✅

### Test Case 6.1: Create Text Story
**Steps:**
1. Click "Stories" in navigation
2. Click "New Story"
3. Enter story text
4. Select background color
5. Click "Post Story"

**Expected Result:**
- Story created
- +10 reputation points awarded
- Expires in 24 hours
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 6.2: View My Stories
**Steps:**
1. Go to Stories → My Stories tab

**Expected Result:**
- Shows all your active stories
- Displays story preview
- Shows view count
- Shows expiration time

**Status:** ⏳ To Test

---

### Test Case 6.3: View Story Viewers
**Steps:**
1. Go to My Stories
2. Click "Views" on a story

**Expected Result:**
- Shows list of users who viewed
- Shows view timestamp
- Shows viewer username

**Status:** ⏳ To Test (needs another account to view)

---

### Test Case 6.4: Delete Story
**Steps:**
1. Go to My Stories
2. Click "Delete"
3. Confirm deletion

**Expected Result:**
- Story deleted immediately
- Removed from database
- Success message shown

**Status:** ⏳ To Test

---

### Test Case 6.5: View Stories Feed
**Steps:**
1. Go to Stories → Feed tab

**Expected Result:**
- Shows stories from connections
- Displays user avatars/initials
- Shows unread indicator (gradient ring)
- Viewed stories show gray ring

**Status:** ⏳ To Test (needs connection with stories)

---

### Test Case 6.6: View Connection's Stories
**Steps:**
1. Go to Stories Feed
2. Click on a user's story ring

**Expected Result:**
- Opens story viewer
- Shows story with background color
- Shows author name and timestamp
- Shows "Close" button

**Status:** ⏳ To Test (needs connection with stories)

---

### Test Case 6.7: Story Auto-Expiration
**Steps:**
1. Create a story
2. Wait 24 hours (or manually change expires_at in database)
3. Try to view expired story

**Expected Result:**
- Story automatically deleted
- "Story has expired" message
- Removed from database

**Status:** ⏳ To Test (manual database edit needed)

---

### Test Case 6.8: Story View Tracking
**Steps:**
1. User A creates story
2. User B (connection) views story
3. User A checks story viewers

**Expected Result:**
- User B appears in viewers list
- View timestamp recorded
- View count increases

**Status:** ⏳ To Test (needs 2 accounts)

---

## Module 7: Trust & Reputation System ✅

### Test Case 7.1: View Trust Level
**Steps:**
1. Go to Profile page

**Expected Result:**
- Shows current points
- Shows trust level badge (🌱 Newcomer, etc.)
- Shows progress bar to next level
- Shows percentage progress

**Status:** ⏳ To Test

---

### Test Case 7.2: Earn Points - Throw Bottle
**Steps:**
1. Note current points
2. Throw a bottle
3. Check points again

**Expected Result:**
- Points increase by +5
- Progress bar updates

**Status:** ⏳ To Test

---

### Test Case 7.3: Earn Points - Keep Bottle
**Steps:**
1. Note current points
2. Keep a bottle
3. Check points again

**Expected Result:**
- Points increase by +10
- Progress bar updates

**Status:** ⏳ To Test

---

### Test Case 7.4: Earn Points - Send Message
**Steps:**
1. Note current points
2. Send a chat message
3. Check points again

**Expected Result:**
- Points increase by +2
- Progress bar updates

**Status:** ⏳ To Test

---

### Test Case 7.5: Earn Points - Create Journal
**Steps:**
1. Note current points
2. Create a journal
3. Check points again

**Expected Result:**
- Points increase by +15
- Progress bar updates

**Status:** ⏳ To Test

---

### Test Case 7.6: Earn Points - Create Story
**Steps:**
1. Note current points
2. Create a story
3. Check points again

**Expected Result:**
- Points increase by +10
- Progress bar updates

**Status:** ⏳ To Test

---

### Test Case 7.7: Trust Level Progression
**Steps:**
1. Start with 0 points (Newcomer 🌱)
2. Earn 51 points
3. Check trust level

**Expected Result:**
- Level changes to Explorer 🔍
- Badge updates on profile

**Status:** ⏳ To Test (accumulate points)

---

## Module 8: AI-Powered Features ✅

### Test Case 8.1: AI Translation - Basic
**Steps:**
1. Set User A language to English
2. Set User B language to Spanish
3. User A sends "Hello, how are you?"

**Expected Result:**
- User B sees: "Hola, ¿cómo estás?"
- Translation indicator present
- Original message saved in database

**Status:** ⏳ To Test (needs 2 accounts, Gemini API key)

---

### Test Case 8.2: AI Hate Speech - Bottle
**Steps:**
1. Try to throw bottle with offensive words
2. Submit

**Expected Result:**
- AI detects inappropriate content
- Bottle NOT created
- Error message displayed

**Status:** ⏳ To Test (needs Gemini API key)

---

### Test Case 8.3: AI Hate Speech - Chat
**Steps:**
1. Try to send offensive message in chat
2. Press send

**Expected Result:**
- AI blocks message
- Alert shown
- Message NOT sent

**Status:** ⏳ To Test (needs Gemini API key)

---

### Test Case 8.4: AI Hate Speech - Journal
**Steps:**
1. Try to create journal with inappropriate content
2. Click Create

**Expected Result:**
- AI blocks journal creation
- Error message shown
- Journal NOT created

**Status:** ⏳ To Test (needs Gemini API key)

---

## Module 9: Safety & Privacy Module ✅

### Test Case 9.1: Journal Privacy - Private
**Steps:**
1. User A creates PRIVATE journal
2. Login as User B (not connected)
3. Check Discover page

**Expected Result:**
- User B CANNOT see User A's private journal
- Journal not visible anywhere to User B

**Status:** ⏳ To Test (needs 2 accounts)

---

### Test Case 9.2: Journal Privacy - Connections
**Steps:**
1. User A creates CONNECTIONS journal
2. User B is connected to User A
3. User B checks Connections Journals

**Expected Result:**
- User B CAN see User A's connections journal
- Visible in Connections tab

**Status:** ⏳ To Test (needs 2 connected accounts)

---

### Test Case 9.3: Journal Privacy - Public
**Steps:**
1. User A creates PUBLIC journal
2. Login as any user
3. Check Discover page

**Expected Result:**
- Any user can see public journal
- Visible in Discover tab

**Status:** ⏳ To Test (needs 2 accounts)

---

### Test Case 9.4: Story Visibility
**Steps:**
1. User A creates story
2. User B (connected) checks Stories Feed
3. User C (NOT connected) checks Stories Feed

**Expected Result:**
- User B CAN see User A's story
- User C CANNOT see User A's story
- Connection-based visibility working

**Status:** ⏳ To Test (needs 3 accounts)

---

### Test Case 9.5: Content Flagging
**Steps:**
1. Try to post inappropriate content
2. Check database content_flags table

**Expected Result:**
- Inappropriate content blocked
- Entry created in content_flags table
- Severity level recorded

**Status:** ⏳ To Test (needs database access)

---

## Navigation & UI Tests ✅

### Test Case 10.1: Navigation Menu
**Steps:**
1. Login to application
2. Check navigation bar

**Expected Result:**
- Shows all links: Dashboard, Profile, Throw Bottle, Bottle Pool, Connections, Chats, Journals, Stories, Logout
- All links working

**Status:** ⏳ To Test

---

### Test Case 10.2: Responsive Design
**Steps:**
1. Open app in different screen sizes
2. Test on mobile view

**Expected Result:**
- Layout adapts to screen size
- All features accessible
- No broken layouts

**Status:** ⏳ To Test

---

### Test Case 10.3: Flash Messages
**Steps:**
1. Perform various actions
2. Check for feedback messages

**Expected Result:**
- Success messages show in green
- Error messages show in red
- Messages are clear and helpful

**Status:** ⏳ To Test

---

## Database Tests ✅

### Test Case 11.1: Data Persistence
**Steps:**
1. Create content (bottle, journal, story)
2. Logout and login again
3. Check if content persists

**Expected Result:**
- All data saved correctly
- Data persists across sessions
- No data loss

**Status:** ⏳ To Test

---

### Test Case 11.2: Relationships
**Steps:**
1. Keep a bottle
2. Check database

**Expected Result:**
- Bottle status updated
- Conversation created
- Foreign keys intact

**Status:** ⏳ To Test

---

## Performance Tests ✅

### Test Case 12.1: Page Load Times
**Steps:**
1. Navigate to different pages
2. Measure load time

**Expected Result:**
- Pages load within 2 seconds
- No significant delays
- Smooth navigation

**Status:** ⏳ To Test

---

### Test Case 12.2: Real-Time Chat Performance
**Steps:**
1. Send multiple messages quickly
2. Check message delivery

**Expected Result:**
- Messages deliver instantly
- No lag or delay
- WebSocket stable

**Status:** ⏳ To Test

---

## Security Tests ✅

### Test Case 13.1: Password Security
**Steps:**
1. Check database users table
2. View password_hash column

**Expected Result:**
- Passwords are hashed (not plain text)
- Using bcrypt hashing
- Cannot reverse hash

**Status:** ⏳ To Test

---

### Test Case 13.2: Session Management
**Steps:**
1. Login
2. Close browser
3. Reopen and try to access protected page

**Expected Result:**
- Session maintained (if configured)
- Or requires re-login (for security)

**Status:** ⏳ To Test

---

### Test Case 13.3: Authorization
**Steps:**
1. Try to access another user's private content directly (URL manipulation)

**Expected Result:**
- Access denied
- Redirected or error shown
- Cannot view unauthorized content

**Status:** ⏳ To Test

---

## 📊 Summary

**Total Test Cases:** 65+
**Modules Covered:** 9/9
**Priority Tests:** All core functionality
**Status:** Ready for testing

---

## 🎯 Testing Priority

**HIGH PRIORITY (Must Test):**
1. Authentication (Login/Register)
2. Bottle System (Throw/Keep)
3. Real-Time Chat
4. AI Translation
5. AI Hate Speech Detection
6. Journals (CRUD)
7. Stories (CRUD)
8. Reputation System

**MEDIUM PRIORITY:**
9. Privacy Settings
10. Navigation
11. UI/UX

**LOW PRIORITY:**
12. Performance
13. Edge Cases

---

**Next Step:** Run these tests systematically and document results!
