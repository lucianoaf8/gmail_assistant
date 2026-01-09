# Gmail Fetcher - Complete Implementation Roadmap

**Roadmap Date:** 2025-10-08 18:44
**Vision:** Advanced email management system with database storage, classification, dashboards, and automated reporting
**Status:** 80% Complete → 100% Complete (6-8 weeks)

---

## Vision Breakdown

### What You Want (Your Words)
- **Fetch/organize/move/delete emails** with advanced filters
- **Database storage layer** as primary data store
- **Email classification/categorization** with segmentation
- **Summary reports and dashboards** for insights
- **Email delivery of reports** automated

### What Already Exists ✅
- ✅ **Gmail API integration** - Full authentication, search, fetch
- ✅ **Email organization** - By date, sender, custom
- ✅ **Delete capability** - Query-based, presets, batch deletion
- ✅ **Database schema** - SQLite with classification columns, FTS5
- ✅ **Classification system** - 8 primary + 11 domain categories
- ✅ **Analysis engine** - Temporal, sender, content analysis
- ✅ **Report generation** - JSON output with insights

### What's Missing ❌
- ❌ **Advanced filter builder** - Visual/programmatic filter creation
- ❌ **Move emails** - Gmail label management
- ❌ **Database-primary workflow** - Currently file-centric
- ❌ **Custom segmentation** - User-defined classification rules
- ❌ **Dashboard UI** - Web interface for visualization
- ❌ **Email delivery** - SMTP integration for reports

---

## Phase-Based Implementation Plan

### Phase 1: Foundation Cleanup (Week 1)
**Goal:** Eliminate technical debt, consolidate code, establish clean foundation

#### 1.1 Code Consolidation
**Files to Merge/Delete:**

```bash
# Delete duplicate implementations
DELETE _to_implement/gmail_emails_deletion/
DELETE _to_implement/daily_summary/
DELETE trash/ (archive if needed)

# Consolidate deletion scripts
MERGE scripts/clean_unread_inbox.py → src/deletion/deleter.py
MERGE scripts/fresh_start.py → src/deletion/deleter.py
DELETE scripts/setup/setup_gmail_deletion.py (duplicate)

# Consolidate analysis scripts
MERGE scripts/analysis/daily_email_analysis.py → src/analysis/daily_email_analyzer.py
MERGE scripts/analysis/setup_analysis.py → src/analysis/setup.py

# Consolidate test files
ORGANIZE tests/ by module (test_core_, test_analysis_, test_deletion_)
DELETE duplicate test files
```

**Action Items:**
- [ ] Create backup of `_to_implement/` and `trash/` (just in case)
- [ ] Extract any useful code from duplicates before deletion
- [ ] Merge deletion functionality into single module
- [ ] Merge analysis functionality into single module
- [ ] Update imports across codebase
- [ ] Run existing tests to ensure nothing breaks

**Deliverables:**
- Cleaned codebase (50+ fewer files)
- Single source of truth for each feature
- Updated documentation reflecting new structure

#### 1.2 Dependency Management
**Files to Create:**

```bash
requirements.lock           # Pinned versions for reproducibility
.python-version            # Python 3.12 specification
pyproject.toml             # Modern Python packaging
```

**Action Items:**
- [ ] Create `requirements.lock` with pinned versions
- [ ] Add `.python-version` file (3.12.10)
- [ ] Create `pyproject.toml` for modern packaging
- [ ] Document setup process in README
- [ ] Test fresh install on clean environment

**Deliverables:**
- Reproducible environment
- Clear setup documentation
- No dependency conflicts

#### 1.3 Git Repository Initialization
**Currently:** Not a git repository (verified)

**Action Items:**
- [ ] `git init` in project root
- [ ] Create `.gitignore` (credentials, tokens, data, __pycache__, etc.)
- [ ] Create `.gitattributes` (line endings, diff settings)
- [ ] Initial commit with clean codebase
- [ ] Create `dev` branch for active work
- [ ] Document git workflow in CONTRIBUTING.md

**Deliverables:**
- Version control established
- Clean git history
- Branch strategy documented

---

### Phase 2: Database-Centric Architecture (Week 2)
**Goal:** Make SQLite the primary data store, files become secondary/optional

#### 2.1 Database Facade Layer
**Files to Create:**

```python
# src/database/db_facade.py
class EmailDatabase:
    """Single interface for all database operations"""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.ensure_schema()

    def insert_email(self, email_data: Dict) -> int:
        """Insert single email, return email_id"""

    def insert_batch(self, emails: List[Dict]) -> List[int]:
        """Bulk insert with transaction"""

    def update_classification(self, email_id: int, classification: Dict):
        """Update classification columns"""

    def search(self, query: str = None, filters: Dict = None) -> pd.DataFrame:
        """Universal search interface (FTS5 + filters)"""

    def get_stats(self) -> Dict:
        """Get database statistics"""

    def export_to_files(self, output_dir: Path, format: str = 'markdown'):
        """Optional: Export database to files"""
```

**Action Items:**
- [ ] Create `src/database/db_facade.py`
- [ ] Implement core CRUD operations
- [ ] Add full-text search wrapper
- [ ] Add export functionality
- [ ] Write comprehensive tests (mock database)

**Deliverables:**
- Single database interface
- 90% test coverage
- Documentation with examples

#### 2.2 Refactor Gmail Fetcher
**Files to Modify:**

```python
# src/core/gmail_fetcher.py (REFACTOR)

class GmailFetcher:
    def __init__(self, credentials_file: str, db: EmailDatabase):
        self.auth = ReadOnlyGmailAuth(credentials_file)
        self.db = db  # NEW: Database connection

    def download_emails(self, query: str, max_emails: int = 100) -> int:
        """Download emails directly to database"""

        # Search messages
        message_ids = self.search_messages(query, max_emails)

        # Process in batches
        batch = []
        for msg_id in message_ids:
            email_data = self._fetch_and_parse(msg_id)
            batch.append(email_data)

            if len(batch) >= 100:
                self.db.insert_batch(batch)
                batch = []

        # Insert remaining
        if batch:
            self.db.insert_batch(batch)

        return len(message_ids)

    def export_to_files(self, email_ids: List[int], output_dir: Path):
        """OPTIONAL: Export specific emails to files"""
        # Now secondary, not primary
```

**Action Items:**
- [ ] Add `EmailDatabase` parameter to `GmailFetcher.__init__`
- [ ] Refactor `download_emails` to insert to database
- [ ] Make file export optional (new method)
- [ ] Update CLI to use database-first workflow
- [ ] Update documentation

**Deliverables:**
- Database-first email fetching
- File export as optional feature
- Backward compatibility maintained

#### 2.3 Data Migration Scripts
**Files to Create:**

```python
# scripts/migrate_files_to_db.py
"""Migrate existing EML/Markdown files to database"""

def migrate_directory(source_dir: Path, db: EmailDatabase):
    """Scan directory and import all emails"""

    for file_path in source_dir.rglob('*.eml'):
        email_data = parse_eml_file(file_path)
        db.insert_email(email_data)

    for file_path in source_dir.rglob('*.md'):
        email_data = parse_markdown_file(file_path)
        db.insert_email(email_data)

# scripts/verify_migration.py
"""Verify database integrity after migration"""

def verify_migration(source_dir: Path, db: EmailDatabase):
    """Compare file count vs database count"""
    # Verification logic
```

**Action Items:**
- [ ] Create migration script for existing backups
- [ ] Add verification script
- [ ] Test migration on sample data
- [ ] Document migration process
- [ ] Run full migration on production data

**Deliverables:**
- All existing emails in database
- Verified data integrity
- Migration playbook documented

---

### Phase 3: Advanced Features (Weeks 3-4)
**Goal:** Implement missing features from vision

#### 3.1 Advanced Filter Builder
**Files to Create:**

```python
# src/filters/filter_builder.py

class FilterBuilder:
    """Build and manage complex email filters"""

    def __init__(self, db: EmailDatabase):
        self.db = db
        self.filters_table = 'saved_filters'

    def build_query(self, filters: Dict) -> str:
        """
        Convert filter dict to SQL WHERE clause

        filters = {
            'sender': 'newsletter@',
            'date_range': ('2025-01-01', '2025-12-31'),
            'categories': ['Newsletter', 'Marketing'],
            'priority': ['High', 'Medium'],
            'has_unsubscribe': True,
            'content_contains': ['AI', 'machine learning']
        }
        """
        clauses = []

        if 'sender' in filters:
            clauses.append(f"sender LIKE '%{filters['sender']}%'")

        if 'date_range' in filters:
            start, end = filters['date_range']
            clauses.append(f"parsed_date BETWEEN '{start}' AND '{end}'")

        if 'categories' in filters:
            cats = "','".join(filters['categories'])
            clauses.append(f"primary_category IN ('{cats}')")

        # ... more filter types

        return ' AND '.join(clauses)

    def save_filter(self, name: str, filters: Dict, description: str = ''):
        """Save filter for reuse"""
        self.db.conn.execute('''
            INSERT INTO saved_filters (name, filters, description)
            VALUES (?, ?, ?)
        ''', (name, json.dumps(filters), description))

    def list_filters(self) -> List[Dict]:
        """Get all saved filters"""
        return [dict(row) for row in self.db.conn.execute(
            'SELECT * FROM saved_filters'
        )]

    def apply_filter(self, name: str) -> pd.DataFrame:
        """Apply saved filter and return results"""
        filter_row = self.db.conn.execute(
            'SELECT filters FROM saved_filters WHERE name = ?', (name,)
        ).fetchone()

        filters = json.loads(filter_row[0])
        query = self.build_query(filters)

        return self.db.conn.execute(
            f'SELECT * FROM emails WHERE {query}'
        ).fetchall()
```

**CLI Integration:**

```python
# main.py (add filter subcommand)

filter_parser = subparsers.add_parser('filter', help='Manage email filters')
filter_subparsers = filter_parser.add_subparsers(dest='filter_action')

# Create filter
create_parser = filter_subparsers.add_parser('create', help='Create new filter')
create_parser.add_argument('--name', required=True)
create_parser.add_argument('--sender', help='Filter by sender pattern')
create_parser.add_argument('--category', help='Filter by category')
create_parser.add_argument('--date-range', nargs=2, help='Start and end dates')

# List filters
list_parser = filter_subparsers.add_parser('list', help='List saved filters')

# Apply filter
apply_parser = filter_subparsers.add_parser('apply', help='Apply saved filter')
apply_parser.add_argument('name', help='Filter name')
apply_parser.add_argument('--export', help='Export results to file')
```

**Action Items:**
- [ ] Create `src/filters/filter_builder.py`
- [ ] Add `saved_filters` table to database schema
- [ ] Implement filter query builder
- [ ] Implement save/load/list operations
- [ ] Add CLI integration
- [ ] Write tests for filter logic
- [ ] Document filter syntax

**Deliverables:**
- Full filter management system
- CLI interface
- Saved filter persistence
- Documentation

#### 3.2 Gmail Label Manager
**Files to Create:**

```python
# src/labels/label_manager.py

class GmailLabelManager:
    """Manage Gmail labels and move emails"""

    def __init__(self, service, db: EmailDatabase):
        self.service = service  # Gmail API service
        self.db = db

    def list_labels(self) -> List[Dict]:
        """Get all Gmail labels"""
        results = self.service.users().labels().list(userId='me').execute()
        return results.get('labels', [])

    def create_label(self, name: str, parent_id: str = None) -> str:
        """Create new Gmail label"""
        label = {
            'name': name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        if parent_id:
            label['parent'] = parent_id

        result = self.service.users().labels().create(
            userId='me', body=label
        ).execute()

        return result['id']

    def move_to_label(self, email_ids: List[str], label_id: str):
        """Move emails to specific label"""
        body = {
            'ids': email_ids,
            'addLabelIds': [label_id],
            'removeLabelIds': ['INBOX']
        }

        self.service.users().messages().batchModify(
            userId='me', body=body
        ).execute()

    def auto_label_by_classification(self):
        """Auto-create labels from classifications and apply"""

        # Get unique categories from database
        categories = self.db.conn.execute(
            'SELECT DISTINCT primary_category FROM emails'
        ).fetchall()

        # Create label for each category
        label_map = {}
        for (category,) in categories:
            label_id = self.create_label(f'Auto/{category}')
            label_map[category] = label_id

        # Apply labels based on classification
        for category, label_id in label_map.items():
            email_ids = self.db.conn.execute(
                'SELECT gmail_id FROM emails WHERE primary_category = ?',
                (category,)
            ).fetchall()

            self.move_to_label([e[0] for e in email_ids], label_id)
```

**CLI Integration:**

```python
# main.py (add labels subcommand)

labels_parser = subparsers.add_parser('labels', help='Manage Gmail labels')
labels_subparsers = labels_parser.add_subparsers(dest='label_action')

# List labels
list_parser = labels_subparsers.add_parser('list', help='List all labels')

# Create label
create_parser = labels_subparsers.add_parser('create', help='Create label')
create_parser.add_argument('name', help='Label name')
create_parser.add_argument('--parent', help='Parent label ID')

# Move emails
move_parser = labels_subparsers.add_parser('move', help='Move emails to label')
move_parser.add_argument('--filter', help='Filter name to select emails')
move_parser.add_argument('--label', required=True, help='Target label')

# Auto-label
auto_parser = labels_subparsers.add_parser('auto', help='Auto-label by classification')
auto_parser.add_argument('--dry-run', action='store_true')
```

**Action Items:**
- [ ] Create `src/labels/label_manager.py`
- [ ] Implement Gmail API label operations
- [ ] Add auto-labeling based on classification
- [ ] Add CLI integration
- [ ] Write tests (mock Gmail API)
- [ ] Document label operations

**Deliverables:**
- Full label management
- Auto-labeling from classification
- CLI interface
- Documentation

#### 3.3 Report Generator & Email Delivery
**Files to Create:**

```python
# src/reports/report_generator.py

class ReportGenerator:
    """Generate reports in various formats"""

    def __init__(self, db: EmailDatabase):
        self.db = db

    def generate_html(self, analysis_results: Dict) -> str:
        """Generate HTML report with charts"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Analysis Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ padding: 10px; background: #f0f0f0; margin: 10px 0; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Email Analysis Report</h1>
            <div class="metric">
                <h2>Summary</h2>
                <p>Total Emails: {analysis_results['metadata']['total_emails']:,}</p>
                <p>Analysis Date: {analysis_results['metadata']['analysis_timestamp']}</p>
            </div>

            <div class="chart">
                <h2>Category Distribution</h2>
                <div id="category-chart"></div>
                <script>
                    var data = [{json.dumps(self._create_category_chart(analysis_results))}];
                    Plotly.newPlot('category-chart', data);
                </script>
            </div>

            <div class="chart">
                <h2>Temporal Patterns</h2>
                <div id="temporal-chart"></div>
                <script>
                    var data = [{json.dumps(self._create_temporal_chart(analysis_results))}];
                    Plotly.newPlot('temporal-chart', data);
                </script>
            </div>

            <div class="metric">
                <h2>Top Recommendations</h2>
                <ul>
                {''.join([f"<li>{r['recommendation']}</li>"
                          for r in analysis_results['insights']['recommendations'][:5]])}
                </ul>
            </div>
        </body>
        </html>
        """

        return html

    def generate_pdf(self, html_report: str) -> bytes:
        """Convert HTML to PDF using weasyprint"""
        from weasyprint import HTML
        return HTML(string=html_report).write_pdf()

    def send_email(self, report: str, recipients: List[str],
                   subject: str = 'Email Analysis Report'):
        """Send report via SMTP"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        # Load SMTP config from environment or config file
        smtp_config = self._load_smtp_config()

        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_address']
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject

        # Attach HTML report
        msg.attach(MIMEText(report, 'html'))

        # Attach PDF if requested
        if smtp_config.get('attach_pdf'):
            pdf = self.generate_pdf(report)
            pdf_attachment = MIMEApplication(pdf, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment',
                                     filename='email_report.pdf')
            msg.attach(pdf_attachment)

        # Send email
        with smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port']) as server:
            server.login(smtp_config['username'], smtp_config['password'])
            server.sendmail(smtp_config['from_address'], recipients, msg.as_string())

# config/smtp_config.json
{
    "host": "smtp.gmail.com",
    "port": 465,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_address": "your-email@gmail.com",
    "attach_pdf": true
}
```

**CLI Integration:**

```python
# main.py (extend analyze subcommand)

analysis_parser.add_argument('--generate-report', action='store_true',
                            help='Generate HTML report')
analysis_parser.add_argument('--send-email', nargs='+',
                            help='Email addresses to send report to')
analysis_parser.add_argument('--smtp-config',
                            default='config/smtp_config.json',
                            help='SMTP configuration file')
```

**Action Items:**
- [ ] Create `src/reports/report_generator.py`
- [ ] Implement HTML report generation with Plotly charts
- [ ] Implement PDF generation (optional: weasyprint)
- [ ] Implement SMTP email delivery
- [ ] Create SMTP config template
- [ ] Add CLI integration
- [ ] Write tests (mock SMTP)
- [ ] Document report generation

**Deliverables:**
- HTML report generation
- PDF export (optional)
- Email delivery system
- CLI integration
- Documentation

---

### Phase 4: Dashboard & Visualization (Weeks 5-6)
**Goal:** Interactive web dashboard for email insights

#### 4.1 Dash Dashboard Implementation
**Files to Create:**

```python
# src/dashboard/app.py

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from database.db_facade import EmailDatabase
from analysis.email_analyzer import EmailAnalysisEngine

# Initialize app
app = dash.Dash(__name__)
db = EmailDatabase('emails.db')
engine = EmailAnalysisEngine({})

# Layout
app.layout = html.Div([
    html.H1('Gmail Fetcher Dashboard'),

    # Date range selector
    html.Div([
        html.Label('Date Range:'),
        dcc.DatePickerRange(
            id='date-range',
            start_date=db.get_stats()['earliest_email'],
            end_date=db.get_stats()['latest_email']
        )
    ]),

    # Category filter
    html.Div([
        html.Label('Categories:'),
        dcc.Dropdown(
            id='category-filter',
            options=[{'label': c, 'value': c}
                     for c in db.get_categories()],
            multi=True
        )
    ]),

    # Summary metrics
    html.Div(id='summary-metrics', className='metrics-row'),

    # Charts
    dcc.Graph(id='category-distribution'),
    dcc.Graph(id='temporal-pattern'),
    dcc.Graph(id='sender-analysis'),
    dcc.Graph(id='content-metrics'),

    # Top senders table
    html.Div(id='top-senders-table'),

    # Recommendations
    html.Div(id='recommendations')
])

# Callbacks
@app.callback(
    [Output('category-distribution', 'figure'),
     Output('temporal-pattern', 'figure'),
     Output('sender-analysis', 'figure'),
     Output('content-metrics', 'figure'),
     Output('summary-metrics', 'children'),
     Output('top-senders-table', 'children'),
     Output('recommendations', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('category-filter', 'value')]
)
def update_dashboard(start_date, end_date, categories):
    # Query database
    df = db.search(filters={
        'date_range': (start_date, end_date),
        'categories': categories
    })

    if df.empty:
        return [go.Figure()] * 4 + [html.Div('No data')] * 3

    # Run analysis
    df_classified = engine.classify_emails(df)
    temporal = engine.analyze_temporal_patterns(df_classified)
    sender = engine.analyze_senders(df_classified)
    content = engine.analyze_content(df_classified)

    # Create visualizations
    fig_category = px.pie(
        df_classified,
        names='category',
        title='Category Distribution'
    )

    fig_temporal = px.line(
        df_classified.groupby(df_classified['date_received'].dt.date).size().reset_index(),
        x='date_received',
        y=0,
        title='Daily Email Volume'
    )

    fig_sender = px.bar(
        df_classified['sender'].value_counts().head(20).reset_index(),
        x='count',
        y='sender',
        title='Top 20 Senders',
        orientation='h'
    )

    fig_content = px.histogram(
        df_classified,
        x='content_length',
        nbins=50,
        title='Content Length Distribution'
    )

    # Summary metrics
    metrics = html.Div([
        html.Div([
            html.H3(len(df_classified)),
            html.P('Total Emails')
        ], className='metric-card'),
        html.Div([
            html.H3(df_classified['sender'].nunique()),
            html.P('Unique Senders')
        ], className='metric-card'),
        html.Div([
            html.H3(f"{sender['automation_analysis']['automation_rate']:.1f}%"),
            html.P('Automated')
        ], className='metric-card')
    ])

    # Top senders table
    top_senders = html.Table([
        html.Thead(html.Tr([
            html.Th('Sender'),
            html.Th('Count'),
            html.Th('Category')
        ])),
        html.Tbody([
            html.Tr([
                html.Td(sender),
                html.Td(count),
                html.Td(df_classified[df_classified['sender']==sender]['category'].iloc[0])
            ])
            for sender, count in df_classified['sender'].value_counts().head(10).items()
        ])
    ])

    # Recommendations
    insights = engine.generate_insights({
        'temporal_analysis': temporal,
        'sender_analysis': sender,
        'content_analysis': content,
        'classification_summary': df_classified['category'].value_counts().to_dict()
    })

    recommendations = html.Ul([
        html.Li(rec['recommendation'])
        for rec in insights.get('recommendations', [])[:5]
    ])

    return (
        fig_category,
        fig_temporal,
        fig_sender,
        fig_content,
        metrics,
        top_senders,
        recommendations
    )

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
```

**Styling:**

```css
/* src/dashboard/assets/style.css */

body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background: #f5f5f5;
}

.metrics-row {
    display: flex;
    gap: 20px;
    margin: 20px 0;
}

.metric-card {
    flex: 1;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.metric-card h3 {
    font-size: 2em;
    margin: 0;
    color: #2c3e50;
}

.metric-card p {
    margin: 10px 0 0 0;
    color: #7f8c8d;
}

table {
    width: 100%;
    background: white;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background: #2c3e50;
    color: white;
}
```

**Action Items:**
- [ ] Create `src/dashboard/app.py`
- [ ] Implement Dash layout with charts
- [ ] Add interactivity (date range, filters)
- [ ] Create CSS styling
- [ ] Add real-time updates (optional)
- [ ] Deploy dashboard (Docker or local)
- [ ] Write documentation

**Deliverables:**
- Interactive web dashboard
- Real-time data visualization
- User-friendly interface
- Deployment guide

---

### Phase 5: Testing & Documentation (Weeks 7-8)
**Goal:** Comprehensive testing and documentation

#### 5.1 Test Infrastructure
**Files to Create:**

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70

# conftest.py (fixtures)
import pytest
from database.db_facade import EmailDatabase
from unittest.mock import MagicMock

@pytest.fixture
def mock_db():
    """Mock database for testing"""
    db = EmailDatabase(':memory:')
    db.ensure_schema()
    return db

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service"""
    service = MagicMock()
    # Setup mock responses
    return service

@pytest.fixture
def sample_emails():
    """Sample email data for testing"""
    return [
        {
            'gmail_id': 'test123',
            'sender': 'newsletter@example.com',
            'subject': 'Weekly AI News',
            'date_received': '2025-10-01',
            'plain_text_content': 'AI news content...'
        },
        # ... more samples
    ]
```

**Test Coverage Goals:**
- `src/database/` - 95%
- `src/core/` - 90%
- `src/analysis/` - 85%
- `src/filters/` - 90%
- `src/labels/` - 80%
- `src/reports/` - 80%
- `src/dashboard/` - 70%

**Action Items:**
- [ ] Setup pytest infrastructure
- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Add mock Gmail API responses
- [ ] Achieve 70%+ coverage
- [ ] Setup CI/CD (GitHub Actions)

#### 5.2 Documentation
**Files to Create/Update:**

```markdown
# README.md (major update)
- Project overview
- Quick start guide
- Feature showcase
- Installation instructions
- Usage examples

# docs/USER_GUIDE.md
- Complete user guide
- CLI reference
- Dashboard usage
- Filter syntax
- Label management
- Report generation

# docs/API.md
- Python API documentation
- EmailDatabase API
- FilterBuilder API
- LabelManager API
- ReportGenerator API

# docs/DEPLOYMENT.md
- Deployment options
- Docker setup
- Cloud deployment (AWS/GCP/Azure)
- Dashboard hosting
- SMTP configuration

# CONTRIBUTING.md
- Development setup
- Code style guide
- Testing requirements
- PR process
```

**Action Items:**
- [ ] Rewrite README with new features
- [ ] Create comprehensive user guide
- [ ] Document all APIs
- [ ] Create deployment guide
- [ ] Add code examples
- [ ] Create video tutorials (optional)

---

## Success Metrics

### Functionality Metrics
- [x] **Gmail Integration** - OAuth 2.0, search, fetch ✅
- [ ] **Database-Primary** - All emails in SQLite
- [x] **Classification** - 8 primary + 11 domain categories ✅
- [ ] **Advanced Filters** - Saved filters, complex queries
- [ ] **Label Management** - Create, move, auto-label
- [ ] **Report Generation** - HTML reports with charts
- [ ] **Email Delivery** - SMTP integration
- [ ] **Dashboard** - Interactive web UI

### Quality Metrics
- [ ] **Test Coverage** - 70%+ overall
- [ ] **Code Consolidation** - <60 files (from 90+)
- [ ] **Documentation** - Complete user guide
- [ ] **Performance** - <2s for 10k email analysis
- [ ] **No Critical Bugs** - All tests passing

### User Experience Metrics
- [ ] **CLI Simplicity** - <5 commands for common tasks
- [ ] **Dashboard Usability** - <3 clicks for insights
- [ ] **Setup Time** - <10 minutes from clone to running
- [ ] **Documentation Clarity** - <15 min to understand

---

## Risk Mitigation

### Technical Risks
| Risk | Mitigation | Owner |
|------|------------|-------|
| Database migration data loss | Backup files before migration, verification script | Phase 2 |
| Gmail API quota limits | Rate limiting, caching, batch operations | All phases |
| Dashboard performance | Pagination, lazy loading, database indexes | Phase 4 |
| SMTP delivery failures | Retry logic, error handling, logging | Phase 3 |

### Project Risks
| Risk | Mitigation | Owner |
|------|------------|-------|
| Scope creep | Stick to roadmap, defer extras to v2.0 | Project lead |
| Timeline slippage | Weekly progress reviews, adjust priorities | Project lead |
| Integration issues | Incremental testing, CI/CD | All phases |

---

## Next Steps (This Week)

### Day 1-2: Cleanup
1. ✅ Backup `_to_implement/` and `trash/`
2. ✅ Extract useful code from duplicates
3. ✅ Consolidate deletion scripts → `src/deletion/deleter.py`
4. ✅ Consolidate analysis scripts → `src/analysis/`
5. ✅ Delete duplicate files
6. ✅ Update imports, run tests

### Day 3-4: Database Foundation
1. ✅ Create `src/database/db_facade.py`
2. ✅ Implement CRUD operations
3. ✅ Write comprehensive tests
4. ✅ Document API

### Day 5-7: Git & Dependencies
1. ✅ Initialize git repository
2. ✅ Create `.gitignore`, `.gitattributes`
3. ✅ Create `requirements.lock`
4. ✅ Create `pyproject.toml`
5. ✅ Initial commit
6. ✅ Document setup process

---

## Resources Required

### Development Tools
- Python 3.12+
- SQLite (included)
- Git
- pytest
- Dash/Plotly

### External Services
- Gmail API (already configured)
- SMTP server (Gmail or custom)
- Optional: Docker for dashboard hosting

### Time Estimate
- **Phase 1:** 1 week (cleanup, foundation)
- **Phase 2:** 1 week (database-centric)
- **Phase 3:** 2 weeks (advanced features)
- **Phase 4:** 2 weeks (dashboard)
- **Phase 5:** 2 weeks (testing, docs)

**Total: 8 weeks to 100% vision completion**

---

## Final Thoughts

This roadmap takes you from **80% → 100%** vision completion systematically. The key is **database-first architecture** - once that's in place, everything else flows naturally.

**Critical Success Factors:**
1. ✅ Consolidate code first (clean foundation)
2. ✅ Database-centric refactor (single source of truth)
3. ✅ Feature implementation (filters, labels, reports)
4. ✅ Dashboard for visualization
5. ✅ Testing & documentation

**You already have the hard parts working** - classification, analysis, Gmail integration. The remaining work is mostly **integration and UI**.

---

**Roadmap Status:** READY FOR EXECUTION
**Next Action:** Start Phase 1 (Code Consolidation)
