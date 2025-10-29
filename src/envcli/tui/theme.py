"""
Theme and styling configuration for EnvCLI TUI
"""

from rich.theme import Theme

# Color palette
COLORS = {
    "background": "#0E141B",
    "surface": "#1A2332",
    "primary": "#00E676",
    "secondary": "#00BFA5",
    "accent": "#64FFDA",
    "warning": "#FFB300",
    "error": "#FF5252",
    "success": "#00E676",
    "info": "#2196F3",
    "text": "#E0E0E0",
    "text_dim": "#757575",
    "border": "#37474F",
    "border_focus": "#00E676",
}

# Rich theme for text formatting
RICH_THEME = Theme({
    "primary": f"bold {COLORS['primary']}",
    "secondary": f"bold {COLORS['secondary']}",
    "accent": COLORS['accent'],
    "warning": f"bold {COLORS['warning']}",
    "error": f"bold {COLORS['error']}",
    "success": f"bold {COLORS['success']}",
    "info": COLORS['info'],
    "dim": COLORS['text_dim'],
    "key": f"bold {COLORS['accent']}",
    "value": COLORS['text'],
    "masked": COLORS['text_dim'],
})

# CSS for Textual components
TUI_CSS = """
Screen {
    background: #0E141B;
}

Header {
    dock: top;
    height: 3;
    background: #1A2332;
    color: #E0E0E0;
    border-bottom: solid #37474F;
}

Footer {
    dock: bottom;
    height: 3;
    background: #1A2332;
    color: #E0E0E0;
    border-top: solid #37474F;
}

Sidebar {
    dock: left;
    width: 30;
    background: #1A2332;
    border-right: solid #37474F;
}

.sidebar-item {
    padding: 1;
    color: #E0E0E0;
}

.sidebar-item:hover {
    background: #263238;
    color: #00E676;
}

.sidebar-item-active {
    background: #00E676;
    color: #0E141B;
}

ContentPanel {
    background: #0E141B;
    padding: 1 2;
}

Button {
    background: #00E676;
    color: #0E141B;
    border: none;
    min-width: 16;
}

Button:hover {
    background: #00BFA5;
}

Button.-warning {
    background: #FFB300;
}

Button.-error {
    background: #FF5252;
}

Input {
    background: #1A2332;
    border: solid #37474F;
    color: #E0E0E0;
}

Input:focus {
    border: solid #00E676;
}

DataTable {
    background: #1A2332;
    color: #E0E0E0;
}

DataTable > .datatable--header {
    background: #263238;
    color: #00E676;
}

DataTable > .datatable--cursor {
    background: #00E676;
    color: #0E141B;
}

.panel {
    background: #1A2332;
    border: solid #37474F;
    padding: 1;
    margin: 1;
}

.panel-title {
    color: #00E676;
    text-style: bold;
}

.stat-card {
    background: #1A2332;
    border: solid #37474F;
    padding: 1;
    height: 7;
}

.stat-value {
    color: #00E676;
    text-style: bold;
    text-align: center;
}

.stat-label {
    color: #757575;
    text-align: center;
}

.alert {
    background: #1A2332;
    border-left: thick #FFB300;
    padding: 1;
    margin: 1 0;
}

.alert-error {
    border-left: thick #FF5252;
}

.alert-success {
    border-left: thick #00E676;
}

.alert-info {
    border-left: thick #2196F3;
}

.masked {
    color: #757575;
}

.key {
    color: #64FFDA;
    text-style: bold;
}

.value {
    color: #E0E0E0;
}

LoadingIndicator {
    background: #1A233280;
    color: #00E676;
}

.toast {
    background: #1A2332;
    border: solid #00E676;
    padding: 1 2;
}

.toast-error {
    border: solid #FF5252;
}

.toast-warning {
    border: solid #FFB300;
}

.command-palette {
    background: #1A2332;
    border: solid #00E676;
    padding: 1;
}

.quick-search {
    background: #1A2332;
    border: solid #00E676;
}

/* Variables Screen */
.screen-title {
    width: 100%;
    height: 3;
    content-align: center middle;
    background: #1A2332;
    color: #00E676;
    text-style: bold;
}

.stats-bar {
    width: 100%;
    height: 2;
    padding: 0 2;
    background: #0E141B;
}

.action-bar {
    width: 100%;
    height: 3;
    padding: 0 2;
    background: #0E141B;
}

.action-bar Button {
    margin: 0 1;
}

.search-input {
    width: 100%;
    height: 3;
    margin: 0 2;
}

.search-input.hidden {
    display: none;
}

.content-area {
    width: 100%;
    height: 1fr;
    padding: 1 2;
}

VariableList {
    width: 100%;
    height: 100%;
}

.variable-list {
    width: 100%;
    height: 100%;
    background: #1A2332;
    border: solid #37474F;
}

VariableRow {
    width: 100%;
    height: 3;
    padding: 0 1;
    background: #0E141B;
    border-bottom: solid #37474F;
}

VariableRow:hover {
    background: #1A2332;
}

.var-key {
    width: 30%;
    color: #64FFDA;
    text-style: bold;
}

.var-value, .var-value-masked {
    width: 50%;
    color: #E0E0E0;
}

.var-value-masked {
    color: #757575;
}

.var-btn {
    width: 10%;
    margin: 0 1;
}

.editor-title {
    width: 100%;
    height: 2;
    content-align: center middle;
    background: #37474F;
    color: #00E676;
    text-style: bold;
}

VariableEditor {
    width: 60;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

VariableEditor Label {
    width: 100%;
    height: 1;
    color: #64FFDA;
    margin-top: 1;
}

VariableEditor Input {
    width: 100%;
    height: 3;
    margin-bottom: 1;
}

VariableEditor Horizontal {
    width: 100%;
    height: 3;
    align: center middle;
}

VariableEditor Button {
    margin: 0 1;
}

VariableEditor.overlay {
    layer: overlay;
    align: center middle;
}

/* Profiles Screen */
.profile-list {
    width: 100%;
    height: 1fr;
    padding: 2;
    overflow-y: auto;
}

ProfileCard {
    width: 100%;
    height: auto;
    min-height: 12;
    background: #1A2332;
    border: solid #37474F;
    padding: 2;
    margin-bottom: 1;
}

ProfileCard:hover {
    border: solid #00E676;
}

.profile-card-title {
    width: 100%;
    height: auto;
    min-height: 1;
    content-align: left middle;
    text-style: bold;
    margin-bottom: 1;
}

.profile-card-meta {
    width: 100%;
    height: auto;
    min-height: 3;
    padding: 1 0;
    margin-bottom: 1;
}

.profile-card-actions {
    width: 100%;
    height: auto;
    min-height: 3;
    align: center middle;
    padding: 1 0;
}

.profile-card-actions Button {
    margin: 0 1;
    min-width: 12;
}

ProfileCreator {
    width: 60;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

ProfileCreator.overlay {
    layer: overlay;
    align: center middle;
}

.creator-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.creator-actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 2;
}

.creator-actions Button {
    margin: 0 1;
    min-width: 15;
}

.creator-title {
    width: 100%;
    height: 2;
    content-align: center middle;
    background: #37474F;
    color: #00E676;
    text-style: bold;
    margin-bottom: 1;
}

ProfileCreator Label {
    width: 100%;
    height: 1;
    color: #64FFDA;
    margin-top: 1;
}

ProfileCreator Input {
    width: 100%;
    height: 3;
    margin-bottom: 1;
}

ProfileCreator Horizontal {
    width: 100%;
    height: 3;
    align: center middle;
    margin-top: 1;
}

ProfileCreator Button {
    margin: 0 1;
}

ProfileComparison {
    width: 80;
    height: auto;
    max-height: 80%;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
    overflow-y: auto;
}

ProfileComparison.overlay {
    layer: overlay;
    align: center middle;
}

.comparison-title {
    width: 100%;
    height: 2;
    content-align: center middle;
    background: #37474F;
    color: #00E676;
    text-style: bold;
    margin-bottom: 1;
}

.diff-section {
    width: 100%;
    height: auto;
    padding: 1;
    margin-bottom: 1;
}

ProfileComparison Button {
    width: 20;
    margin-top: 1;
}

/* AI Analysis Screen */
.recommendations-list {
    width: 100%;
    height: 1fr;
    padding: 2;
    overflow-y: auto;
}

RecommendationCard {
    width: 100%;
    height: auto;
    min-height: 10;
    background: #1A2332;
    border: solid #37474F;
    padding: 2;
    margin-bottom: 1;
}

RecommendationCard:hover {
    border: solid #64FFDA;
}

.recommendation-title {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

.recommendation-detail {
    width: 100%;
    height: auto;
    padding: 0 1;
    margin-bottom: 1;
}

.recommendation-actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 1;
}

.recommendation-actions Button {
    margin: 0 1;
    min-width: 12;
}

ActionPreview {
    width: 80;
    height: auto;
    max-height: 80%;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
    overflow-y: auto;
}

ActionPreview.overlay {
    layer: overlay;
    align: center middle;
}

.preview-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.preview-empty {
    width: 100%;
    text-align: center;
    color: #757575;
    padding: 2;
}

.preview-actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 2;
}

.preview-actions Button {
    margin: 0 1;
    min-width: 15;
}

#actions-table {
    width: 100%;
    height: auto;
    margin-bottom: 2;
}

.ai-disabled-message {
    width: 100%;
    height: auto;
    padding: 4;
    text-align: center;
    background: #1A2332;
    border: solid #FFB300;
    margin: 2;
}

.placeholder-text {
    width: 100%;
    height: auto;
    padding: 4;
    text-align: center;
    color: #757575;
}

/* Rules & Policies Screen */
.rules-list {
    width: 100%;
    height: 1fr;
    padding: 2;
    overflow-y: auto;
}

.rules-section-title {
    width: 100%;
    height: auto;
    text-style: bold;
    color: #00E676;
    padding: 1 2;
    margin-top: 2;
    margin-bottom: 1;
    background: #0E141B;
}

RuleCard {
    width: 100%;
    height: auto;
    min-height: 10;
    background: #1A2332;
    border: solid #37474F;
    padding: 2;
    margin-bottom: 1;
}

RuleCard:hover {
    border: solid #64FFDA;
}

.rule-title {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

.rule-detail {
    width: 100%;
    height: auto;
    padding: 0 1;
    margin-bottom: 1;
}

.rule-actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 1;
}

.rule-actions Button {
    margin: 0 1;
    min-width: 12;
}

RuleEditor {
    width: 60;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

RuleEditor.overlay {
    layer: overlay;
    align: center middle;
}

.editor-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.editor-actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 2;
}

.editor-actions Button {
    margin: 0 1;
    min-width: 15;
}

RuleEditor Label {
    margin-top: 1;
    margin-bottom: 0;
    color: #64FFDA;
}

RuleEditor Input {
    margin-bottom: 1;
}

/* Encryption Screen */
.encryption-info {
    width: 100%;
    height: auto;
    padding: 1;
}

.encryption-info-text {
    width: 100%;
    height: auto;
    padding: 1;
}

.section-title {
    width: 100%;
    height: 2;
    color: #00E676;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 1;
}

.file-status {
    width: 100%;
    height: 1;
    padding-left: 2;
    margin-bottom: 0;
}

FileSelector {
    width: 80;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

FileSelector.overlay {
    layer: overlay;
    align: center middle;
}

.selector-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.quick-select-label {
    width: 100%;
    color: #64FFDA;
    margin-top: 2;
    margin-bottom: 1;
}

.quick-select-list {
    width: 100%;
    height: auto;
    max-height: 15;
    overflow-y: auto;
    margin-bottom: 2;
}

.quick-select-list Button {
    width: 100%;
    margin-bottom: 1;
}

.selector-actions {
    width: 100%;
    height: 3;
    align: center middle;
}

.selector-actions Button {
    margin: 0 1;
}

KeyManager {
    width: 70;
    height: auto;
    background: #1A2332;
    border: solid #FFB300;
    padding: 2;
}

KeyManager.overlay {
    layer: overlay;
    align: center middle;
}

.manager-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #FFB300;
    margin-bottom: 2;
}

.key-info {
    width: 100%;
    height: auto;
    padding: 1;
    background: #37474F;
    margin-bottom: 2;
}

.key-status {
    width: 100%;
    height: auto;
    padding: 1;
    margin-bottom: 2;
}

.manager-actions {
    width: 100%;
    height: 3;
    align: center middle;
}

.manager-actions Button {
    margin: 0 1;
}

/* Cloud Sync Screen */
.provider-bar {
    width: 100%;
    height: 3;
    align: center middle;
    margin-bottom: 1;
}

.provider-bar Button {
    margin: 0 1;
}

.provider-info-text {
    width: 100%;
    height: auto;
    padding: 1;
}

.sync-instructions {
    width: 100%;
    height: auto;
    padding: 1;
    margin-top: 2;
}

SyncConfigurator {
    width: 70;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

SyncConfigurator.overlay {
    layer: overlay;
    align: center middle;
}

.config-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.config-info {
    width: 100%;
    height: auto;
    padding: 1;
    background: #37474F;
    margin-top: 1;
    margin-bottom: 2;
}

.config-actions {
    width: 100%;
    height: 3;
    align: center middle;
    margin-top: 2;
}

.config-actions Button {
    margin: 0 1;
}

ProviderMenu {
    width: 50;
    height: auto;
    background: #1A2332;
    border: solid #00E676;
    padding: 2;
}

ProviderMenu.overlay {
    layer: overlay;
    align: center middle;
}

.menu-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.menu-operations {
    width: 100%;
    height: auto;
    margin-bottom: 2;
}

.menu-operations Button {
    width: 100%;
    margin-bottom: 1;
}

.menu-actions {
    width: 100%;
    height: 3;
    align: center middle;
}

.menu-actions Button {
    margin: 0 1;
}

/* Settings Screen */
.section-header {
    width: 100%;
    text-align: left;
    text-style: bold;
    color: #00E676;
    margin-top: 2;
    margin-bottom: 1;
    padding: 1;
    background: #1A2332;
}

.section-divider {
    width: 100%;
    height: 1;
    margin-top: 2;
    margin-bottom: 2;
}

.setting-value {
    width: 100%;
    height: auto;
    padding: 1;
    background: #0E141B;
    margin-bottom: 1;
}

.setting-actions {
    width: 100%;
    height: 3;
    align: left middle;
    margin-bottom: 2;
}

.setting-actions Button {
    margin: 0 1 0 0;
}

AIProviderConfig {
    width: 80;
    height: 45;
    background: #1A2332;
    border: thick #00E676;
    padding: 2;
}

AIProviderConfig.overlay {
    layer: overlay;
    align: center middle;
}

#config-scroll {
    width: 100%;
    height: 1fr;
    margin-bottom: 1;
}

.config-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: #00E676;
    margin-bottom: 2;
}

.ai-status {
    width: 100%;
    height: auto;
    padding: 1;
    background: #0E141B;
    margin-bottom: 2;
}

.config-info {
    width: 100%;
    height: auto;
    padding: 1;
    background: #0E141B;
    margin-top: 1;
    margin-bottom: 2;
}

.provider-list {
    width: 100%;
    height: auto;
    margin-bottom: 2;
}

.provider-list Button {
    width: 100%;
    margin-bottom: 1;
}

.config-actions {
    width: 100%;
    height: 3;
    align: center middle;
    margin-top: 1;
}

.config-actions Button {
    margin: 0 1;
}

AIProviderConfig Label {
    width: 100%;
    margin-top: 1;
    margin-bottom: 1;
    color: #E0E0E0;
}

AIProviderConfig Input {
    width: 100%;
    margin-bottom: 2;
}
"""

# Module icons (using Unicode symbols)
MODULE_IOS = {
    "dashboard": "◆",
    "variables": "◉",
    "profiles": "◈",
    "encryption": "◐",
    "ai_analysis": "◎",
    "rules": "◇",
    "cloud_sync": "◭",
    "kubernetes": "◮",
    "rbac": "◪",
    "compliance": "◫",
    "audit": "◬",
    "cicd": "◯",
    "events": "◰",
    "monitoring": "◱",
    "plugins": "◲",
    "analytics": "◳",
    "predict": "◴",
    "settings": "◵",
}

# Status indicators
STATUS_IOS = {
    "success": "+",
    "error": "X",
    "warning": "!",
    "info": "vFO",
    "loading": "@",
    "synced": "@",
    "unsynced": "?",
}

def get_module_icon(module_name: str) -> str:
    """Get icon for a module."""
    return MODULE_IOS.get(module_name, "•")

def get_status_icon(status: str) -> str:
    """Get icon for a status."""
    return STATUS_IOS.get(status, "•")

