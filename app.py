import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
import urllib.parse
from streamlit_option_menu import option_menu

# Initialize database and directories
os.makedirs("database", exist_ok=True)

# Database functions
def create_tables():
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 bio TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Posts table - simplified without image_path
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 author TEXT NOT NULL,
                 title TEXT NOT NULL,
                 content TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 post_id INTEGER NOT NULL,
                 user_id INTEGER NOT NULL,
                 content TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(post_id) REFERENCES posts(id),
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Likes table
    c.execute('''CREATE TABLE IF NOT EXISTS likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 post_id INTEGER NOT NULL,
                 user_id INTEGER NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(post_id) REFERENCES posts(id),
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 UNIQUE(post_id, user_id))''')
    
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
             (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

def get_user(username):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def update_profile(username, bio):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("UPDATE users SET bio = ? WHERE username = ?", 
                 (bio, username))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def add_post(author, title, content, categories=None, tags=None):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("""INSERT INTO posts 
                    (author, title, content) 
                    VALUES (?, ?, ?)""",
                 (author, title, content))
        post_id = c.lastrowid
        conn.commit()
        conn.close()
        return post_id
    except Exception as e:
        st.error(f"Error adding post: {e}")
        return False

def get_all_posts(search_term=None, author=None):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    
    query = "SELECT * FROM posts"
    params = []
    
    if search_term or author:
        query += " WHERE"
        if search_term:
            query += " (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        if author:
            if search_term:
                query += " AND"
            query += " author = ?"
            params.append(author)
    
    query += " ORDER BY id DESC"
    c.execute(query, params)
    posts = c.fetchall()
    conn.close()
    return posts

def get_post_by_id(post_id):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return post

def update_post(post_id, title, content, categories=None, tags=None):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("""UPDATE posts SET 
                    title = ?, content = ? 
                    WHERE id = ?""",
                 (title, content, post_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating post: {e}")
        return False

def delete_post(post_id):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        # First delete comments associated with the post
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        # Then delete the post
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting post: {e}")
        return False

def add_comment(post_id, user_id, content):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding comment: {e}")
        return False

def get_comments(post_id):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("""SELECT comments.*, users.username 
              FROM comments 
              JOIN users ON comments.user_id = users.id 
              WHERE post_id = ? 
              ORDER BY created_at DESC""", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments

def add_like(post_id, user_id):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", 
                 (post_id, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_like(post_id, user_id):
    try:
        conn = sqlite3.connect('database/blog.db')
        c = conn.cursor()
        c.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", 
                 (post_id, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_likes_count(post_id):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def has_user_liked(post_id, user_id):
    conn = sqlite3.connect('database/blog.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?", 
             (post_id, user_id))
    result = c.fetchone() is not None
    conn.close()
    return result

# Initialize database tables
create_tables()

# Streamlit app configuration
st.set_page_config(layout="wide", page_title="GSV Blogs", page_icon="✍")

# Custom CSS with improved colors and styling
st.markdown("""
<style>
:root {
    --primary: #4a6fa5;
    --secondary: #166088;
    --accent: #4fc3f7;
    --text: #333333;
    --light: #f8f9fa;
    --dark: #343a40;
}

/* Main content styling */
.stApp {
    background-color: #f5f5f5;
    color: var(--text);
}

/* Text colors */
h1, h2, h3, h4, h5, h6 {
    color: var(--secondary) !important;
}
p, div, span {
    color: var(--text) !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: white !important;
    color: var(--secondary) !important;
}
[data-testid="stSidebar"] .st-b7 {
    color: var(--secondary) !important;
}

/* Input fields */
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
    background-color: white !important;
    color: var(--dark) !important;
}

/* Buttons */
.stButton>button {
    background-color: var(--primary) !important;
    color: white !important;
    border: none;
    transition: all 0.3s;
}
.stButton>button:hover {
    background-color: var(--secondary) !important;
    transform: scale(1.05);
}

/* Cards */
.post-card {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.post-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

/* Navigation icons */
.nav-icon {
    margin-right: 10px;
    vertical-align: middle;
}

/* Dark mode toggle */
.dark-mode-toggle {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

/* Share buttons */
.share-buttons {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}
.share-button {
    padding: 8px 12px;
    border-radius: 8px;
    color: white !important;
    text-decoration: none !important;
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    font-weight:bold;
}
.twitter-share {
    background-color: #1DA1F2;
}
.whatsapp-share {
    background-color: #25D366;
}

/* Dropdown menu styling */
.stSelectbox>div>div>select {
    background-color: white !important;
    color: var(--dark) !important;
    border: 1px solid var(--primary) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

.stSelectbox>div>div>select:hover {
    border-color: var(--secondary) !important;
}

.stSelectbox>div>div>select:focus {
    box-shadow: 0 0 0 2px rgba(74, 111, 165, 0.2) !important;
    border-color: var(--primary) !important;
}

/* Like button styling */
.like-button {
    background-color: #f5f5f5 !important;
    color: white !important;
    border: 1px solid #ddd !important;
    padding: 5px 10px !important;
    border-radius: 15px !important;
    display: inline-flex !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: all 0.3s !important;
}

.like-button:hover {
    background-color: #f0f0f0 !important;
}

.like-button.liked {
    background-color: #ffebee !important;
    color: #f44336 !important;
    border-color: #f44336 !important;
}

.like-count {
    margin-left: 5px;
    font-size: 14px;
}

/* Responsive layout */
@media (max-width: 768px) {
    .stSidebar {
        width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# User authentication
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px; border-radius: 15px; background-color: var(--light);">
        <h1 style="color: var(--primary);">Welcome to GSV BLOGS ✍</h1>
        <p style="font-size: 18px;">Please login or register to access all blog features</p>       
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.header("User Authentication")
    st.sidebar.write("Please login or register to access all blog features")
    st.header("User Authentication")

    auth_action = st.radio("Select Action", ["Login", "Register"],horizontal=True)

    if auth_action == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user[0]
                st.sidebar.success("Logged in successfully!")
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password.")
                st.error("Invalid username or password.")

    elif auth_action == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.sidebar.success("User registered successfully! Please login.")
                st.success("User registered successfully! Please login.")
            else:
                st.sidebar.error("Username already exists.")
                st.error("Username already exists.")


# Main app
if st.session_state.logged_in:
    # Sidebar controls
    st.sidebar.success(f"Hi, {st.session_state.username}")    
    
    with st.sidebar:
        choice = option_menu(
            menu_title=None,   
            options=["Home", "Posts","Profile", "Contact Us","About"],  # Menu items
            icons=["house", "file-text", "envelope"], # Optional icons (from Bootstrap)
            default_index=0,               # Which item is selected by default
            styles={
                "container": {"padding": "0px","background-color":"white"},
                "icon": {"color": "black", "font-size": "18px"},
                "nav-link": {
                    "background-color":"white",
                    "color":"black",
                    "font-size": "12px",
                    "text-align": "left",
                    "margin-top": "8px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
            }
        )

    if choice == "Home":
        st.markdown('<div style="text-align: center"><h1 class="fade-in main-title">Welcome to GSV BLOGS! ✍</h1></div>', unsafe_allow_html=True)
        search_term = st.text_input("🔍 Search posts")
        posts = get_all_posts(search_term)
            
        if posts:
            for post in posts:
                with st.container():
                    # Like button functionality
                    liked = has_user_liked(post[0], st.session_state.user_id)
                    like_count = get_likes_count(post[0])
                    
                    # Create columns for the title and like button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"<h3>{post[2]}</h3>", unsafe_allow_html=True)
                    with col2:
                        like_key = f"like_{post[0]}"
                        if st.button(f"❤ {like_count}", key=like_key, 
                                   help="Click to like/unlike",
                                   type="primary" if liked else "secondary"):
                            if liked:
                                remove_like(post[0], st.session_state.user_id)
                            else:
                                add_like(post[0], st.session_state.user_id)
                            st.rerun()
                    
                    # Rest of the post content
                    st.markdown(f"""
                    <div class="post-card">
                        <p><strong>Author:</strong> {post[1]} | <strong>Date:</strong> {post[4]}</p>
                        <p>{post[3]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Comments section
                    st.subheader("💬 Comments")
                    comments = get_comments(post[0])
                    for comment in comments:
                        st.markdown(f"""
                        <div style="background-color: var(--light); padding: 10px; border-radius: 8px; margin: 5px 0;">
                            <strong>{comment[5]}:</strong> {comment[3]}
                            <div style="font-size: 0.8em; color: #666;">{comment[4]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Add comment
                    new_comment = st.text_area("Add a comment", key=f"comment_{post[0]}", placeholder="Write your comment here...")
                    if st.button("Post Comment", key=f"post_comment_{post[0]}"):
                        if new_comment.strip():
                            if add_comment(post[0], st.session_state.user_id, new_comment):
                                st.success("Comment added!")
                                st.rerun()
                            else:
                                st.error("Failed to add comment")
                        else:
                            st.warning("Please write a comment before posting")
                    
                    # Share buttons
                    st.markdown("""
                    <div class="share-buttons">
                        <p style="margin-right: 10px; font-weight: bold;">Share:</p>
                        <a href="https://twitter.com/intent/tweet?text=Check%20out%20this%20post:%20{post[2]}" 
                           class="share-button twitter-share" target="_blank">
                            Twitter
                        </a>
                        <a href="https://wa.me/?text=Check%20out%20this%20post:%20{post[2]}" 
                           class="share-button whatsapp-share" target="_blank">
                            WhatsApp
                        </a>
                    </div>
                    """.format(post=post), unsafe_allow_html=True)
                    
                    st.write("---")
        else:
            st.info("No posts available. Be the first to create one!")

    elif choice == "Posts":
        post_action = option_menu(
            menu_title=None,   
            options=["View Posts", "Write Post","Edit Posts", "Delete Posts"],  # Menu items
            default_index=1,
            orientation="horizontal",
            styles={
                "container": {"padding": "0px","background-color":"white"},
                "icon": {"color": "black", "font-size": "18px"},
                "nav-link": {
                    "background-color":"white",
                    "color":"black",
                    "font-size": "12px",
                    "text-align": "left",
                    "margin-top": "8px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
            }
        )
        if post_action == "View Posts":
            search_term = st.text_input("🔍 Search posts")
            posts = get_all_posts(search_term)
            
            if posts:
                for post in posts:
                    with st.container():
                        # Like button functionality
                        liked = has_user_liked(post[0], st.session_state.user_id)
                        like_count = get_likes_count(post[0])
                        
                        # Create columns for the title and like button
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"<h3>{post[2]}</h3>", unsafe_allow_html=True)
                        with col2:
                            like_key = f"like_{post[0]}"
                            if st.button(f"❤ {like_count}", key=like_key, 
                                       help="Click to like/unlike",
                                       type="primary" if liked else "secondary"):
                                if liked:
                                    remove_like(post[0], st.session_state.user_id)
                                else:
                                    add_like(post[0], st.session_state.user_id)
                                st.rerun()
                        
                        # Rest of the post content
                        st.markdown(f"""
                        <div class="post-card">
                            <p><strong>Author:</strong> {post[1]} | <strong>Date:</strong> {post[4]}</p>
                            <p>{post[3]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Comments section
                        st.subheader("💬 Comments")
                        comments = get_comments(post[0])
                        for comment in comments:
                            st.markdown(f"""
                            <div style="background-color: var(--light); padding: 10px; border-radius: 8px; margin: 5px 0;">
                                <strong>{comment[5]}:</strong> {comment[3]}
                                <div style="font-size: 0.8em; color: #666;">{comment[4]}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Add comment
                        new_comment = st.text_area("Add a comment", key=f"comment_{post[0]}", placeholder="Write your comment here...")
                        if st.button("Post Comment", key=f"post_comment_{post[0]}"):
                            if new_comment.strip():
                                if add_comment(post[0], st.session_state.user_id, new_comment):
                                    st.success("Comment added!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add comment")
                            else:
                                st.warning("Please write a comment before posting")
                        
                        # Share buttons
                        st.markdown("""
                        <div class="share-buttons">
                            <p style="margin-right: 10px; font-weight: bold;">Share:</p>
                            <a href="https://twitter.com/intent/tweet?text=Check%20out%20this%20post:%20{post[2]}" 
                               class="share-button twitter-share" target="_blank">
                                Twitter
                            </a>
                            <a href="https://wa.me/?text=Check%20out%20this%20post:%20{post[2]}" 
                               class="share-button whatsapp-share" target="_blank">
                                WhatsApp
                            </a>
                        </div>
                        """.format(post=post), unsafe_allow_html=True)
                        
                        st.write("---")
            else:
                st.info("No posts available. Be the first to create one!")

        elif post_action == "Write Post":
            st.subheader("📝 Create New Post")
            title = st.text_input("Title", placeholder="Enter a catchy title...")
            content = st.text_area("Content", height=300, placeholder="Write your post content here...")
            categories = st.multiselect("Categories", ["Technology", "Travel", "Food", "Lifestyle", "Personal"])
            tags = st.text_input("Tags (comma separated)", placeholder="e.g., tech, programming, web")
            
            if st.button("Publish Post", key="publish_button"):
                if not title or not content:
                    st.error("Title and content are required!")
                else:
                    post_id = add_post(st.session_state.username, title, content, categories, tags)
                    if post_id:
                        st.success("🎉 Post published successfully!")
                        #st.balloons()
                        # st.rerun()
                    else:
                        st.error("Failed to publish post")

        elif post_action == "Edit Posts":
            st.subheader("✏ Edit Your Posts")
            user_posts = get_all_posts(author=st.session_state.username)
            
            if user_posts:
                post_to_edit = st.selectbox("Select post to edit", 
                                          [f"{post[0]} - {post[2]}" for post in user_posts],
                                          key="edit_post_select")
                
                if post_to_edit:
                    post_id = int(post_to_edit.split(" - ")[0])
                    post = get_post_by_id(post_id)
                    
                    if post:
                        title = st.text_input("Title", post[2], key=f"edit_title_{post_id}")
                        content = st.text_area("Content", post[3], height=300, key=f"edit_content_{post_id}")
                        
                        # Get current categories and tags
                        current_categories = []
                        categories = st.multiselect("Categories", ["Technology", "Travel", "Food", "Lifestyle", "Personal"],
                                                  default=current_categories, key=f"edit_categories_{post_id}")
                        
                        tags = st.text_input("Tags (comma separated)", "", key=f"edit_tags_{post_id}")
                        
                        if st.button("Update Post", key=f"update_button_{post_id}"):
                            if update_post(post_id, title, content, categories, tags):
                                st.success("✅ Post updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update post")
            else:
                st.info("You have no posts to edit yet. Create your first post!")

        elif post_action == "Delete Posts":
            st.subheader("🗑 Delete Your Posts")
            user_posts = get_all_posts(author=st.session_state.username)
            
            if user_posts:
                post_to_delete = st.selectbox("Select post to delete", 
                                            [f"{post[0]} - {post[2]}" for post in user_posts],
                                            key="delete_post_select")
                
                if post_to_delete:
                    post_id = int(post_to_delete.split(" - ")[0])
                    post = get_post_by_id(post_id)
                    
                    if post:
                        st.warning(f"⚠ You are about to delete: {post[2]}")
                        st.markdown(f"""
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">
                            {post[3][:200] + "..." if len(post[3]) > 200 else post[3]}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Confirm Delete", key=f"confirm_delete_{post_id}"):
                            if delete_post(post_id):
                                st.success("🗑 Post deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete post")
            else:
                st.info("You have no posts to delete.")

    elif choice == "Profile":
        st.subheader(f"👤 {st.session_state.username}")
        user = get_user(st.session_state.username)
        
        st.markdown("### Bio")
        bio = st.text_area("", user[3] if user and user[3] else "Write something about yourself...", 
                          height=150, key="bio_textarea")
        
        if st.button("Update Profile", key="update_profile_button"):
            if update_profile(st.session_state.username, bio):
                st.success("👍 Profile updated!")
                st.rerun()
            else:
                st.error("Failed to update profile")

    elif choice == "Contact Us":
        st.markdown("""
        <div class="home-content" style="background-color: var(--light); padding: 30px; border-radius: 15px;">
            <h2 style="color: var(--primary);">📧 Contact Us</h2>
            <div style="margin-top: 20px;">
                <p style="font-size: 18px;">📩 <strong>Email:</strong> contact@gsvblogs.com</p>
                <p style="font-size: 18px;">📱 <strong>Phone:</strong> +1 (123) 456-7890</p>
                <p style="font-size: 18px;">🏢 <strong>Address:</strong> 123 Blog Street, Digital City</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif choice == "About":
        st.markdown("""
        <div class="about-container">
            <h1 style="color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 10px;">About GSV BLOGS</h1>
            <p style="font-size: 16px; line-height: 1.6;">
                GSV BLOGS is a community-driven platform dedicated to sharing ideas, stories, and creativity. Our mission is to foster a welcoming environment where writers and readers connect through meaningful content.
            </p>
            <h2 style="color: var(--secondary); margin-top: 30px;">Key Features</h2>
            <ul style="font-size: 16px; line-height: 1.6;">
                <li>Intuitive and beautiful post editor</li>
                <li>Engaging community with comments and likes</li>
                <li>Responsive design for all devices</li>
                <li>Calming water-themed aesthetic</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Add the feature cards section
        st.markdown("""
        <div style="margin-top: 30px; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 250px; max-width: 300px; background-color: rgba(255,255,255,0.8); padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h3 style="color: var(--secondary);">Write Your Story</h3>
                <p>Share your thoughts with our beautiful editor</p>
            </div>
            <div style="flex: 1; min-width: 250px; max-width: 300px; background-color: rgba(255,255,255,0.8); padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h3 style="color: var(--secondary);">Connect with Others</h3>
                <p>Engage with a community of readers and writers</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add the final call-to-action
        st.markdown("""
        <p style="margin-top: 30px; text-align: center; font-size: 18px;">Join us and start sharing your story today!</p>
        """, unsafe_allow_html=True)


    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()