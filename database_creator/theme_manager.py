"""
Theme manager for database creator GUI.
Provides theme support with light and dark modes.
"""
import tkinter as tk
from tkinter import ttk


class ThemeManager:
    """Theme manager for GUI applications."""

    # Theme definitions
    THEMES = {
        'light': {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'button_bg': '#e0e0e0',
            'button_fg': '#000000',
            'entry_bg': '#ffffff',
            'entry_fg': '#000000',
            'select_bg': '#0078d7',
            'select_fg': '#ffffff',
            'treeview_bg': '#ffffff',
            'treeview_fg': '#000000',
            'treeview_select_bg': '#0078d7',
            'treeview_select_fg': '#ffffff',
            'tab_bg': '#f0f0f0',
            'tab_fg': '#000000',
            'tab_active_bg': '#e0e0e0',
            'tab_active_fg': '#000000',
            'label_bg': '#f0f0f0',
            'label_fg': '#000000',
            'statusbar_bg': '#e0e0e0',
            'statusbar_fg': '#000000',
            'highlight_bg': '#e0e0e0',
            'highlight_fg': '#000000',
        },
        'dark': {
            'bg': '#2d2d2d',
            'fg': '#ffffff',
            'button_bg': '#444444',
            'button_fg': '#ffffff',
            'entry_bg': '#3d3d3d',
            'entry_fg': '#ffffff',
            'select_bg': '#0078d7',
            'select_fg': '#ffffff',
            'treeview_bg': '#333333',
            'treeview_fg': '#ffffff',
            'treeview_select_bg': '#0078d7',
            'treeview_select_fg': '#ffffff',
            'tab_bg': '#2d2d2d',
            'tab_fg': '#ffffff',
            'tab_active_bg': '#444444',
            'tab_active_fg': '#ffffff',
            'label_bg': '#2d2d2d',
            'label_fg': '#ffffff',
            'statusbar_bg': '#444444',
            'statusbar_fg': '#ffffff',
            'highlight_bg': '#444444',
            'highlight_fg': '#ffffff',
        }
    }

    def __init__(self, root, config=None):
        """
        Initialize the theme manager.

        Args:
            root (tk.Tk): Root Tkinter window
            config (dict): Configuration dictionary
        """
        self.root = root
        self.config = config or {}
        self.current_theme = self.config.get('theme', 'light')

        # Create theme variable
        self.theme_var = tk.BooleanVar()
        self.theme_var.set(self.current_theme == 'dark')

        # Initialize the style
        self.style = ttk.Style()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom widget styles."""
        # We'll create custom styles for both themes
        for theme_name, theme_colors in self.THEMES.items():
            # Create styles with theme name prefix
            self.style.configure(
                f'{theme_name}.TButton',
                background=theme_colors['button_bg'],
                foreground=theme_colors['button_fg']
            )
            self.style.configure(
                f'{theme_name}.TLabel',
                background=theme_colors['label_bg'],
                foreground=theme_colors['label_fg']
            )
            self.style.configure(
                f'{theme_name}.TFrame',
                background=theme_colors['bg']
            )
            self.style.configure(
                f'{theme_name}.TEntry',
                fieldbackground=theme_colors['entry_bg'],
                foreground=theme_colors['entry_fg']
            )

            # Configure Treeview for this theme
            self.style.configure(
                f'{theme_name}.Treeview',
                background=theme_colors['treeview_bg'],
                foreground=theme_colors['treeview_fg'],
                fieldbackground=theme_colors['treeview_bg']
            )
            self.style.map(
                f'{theme_name}.Treeview',
                background=[('selected', theme_colors['treeview_select_bg'])],
                foreground=[('selected', theme_colors['treeview_select_fg'])]
            )

            # Configure Notebook for this theme
            self.style.configure(
                f'{theme_name}.TNotebook',
                background=theme_colors['bg']
            )
            self.style.configure(
                f'{theme_name}.TNotebook.Tab',
                background=theme_colors['tab_bg'],
                foreground=theme_colors['tab_fg']
            )
            self.style.map(
                f'{theme_name}.TNotebook.Tab',
                background=[('selected', theme_colors['tab_active_bg'])],
                foreground=[('selected', theme_colors['tab_active_fg'])]
            )

            # Configure LabelFrame for this theme
            self.style.configure(
                f'{theme_name}.TLabelframe',
                background=theme_colors['bg']
            )
            self.style.configure(
                f'{theme_name}.TLabelframe.Label',
                background=theme_colors['bg'],
                foreground=theme_colors['fg']
            )

    def apply_theme(self, theme_name=None):
        """
        Apply the specified theme.

        Args:
            theme_name (str, optional): Theme name ('light' or 'dark').
                If not provided, uses the current theme.
        """
        # Use the provided theme or the current one
        theme_name = theme_name or self.current_theme

        # Get theme colors
        theme = self.THEMES.get(theme_name, self.THEMES['light'])

        print(
            "Applying {} theme with colors: {}/{}".format(
                theme_name, theme['bg'], theme['fg']
            )
        )

        # Apply theme to root
        self.root.configure(background=theme['bg'])

        # Apply theme directly to all ttk widgets through style
        self.style.theme_use('clam')  # Use clam as base theme

        # Set base style for all widgets
        self.style.configure(
            '.',
            background=theme['bg'],
            foreground=theme['fg'],
            fieldbackground=theme['entry_bg']
        )

        # Configure Treeview specifically for this theme
        self.style.configure(
            'Treeview',
            background=theme['treeview_bg'],
            foreground=theme['treeview_fg'],
            fieldbackground=theme['treeview_bg']
        )

        self.style.configure(
            'TLabel',
            background=theme['bg'],
            foreground=theme['fg'])
        self.style.configure(
            'TButton',
            background=theme['button_bg'],
            foreground=theme['button_fg'])
        self.style.configure('TFrame', background=theme['bg'])
        self.style.configure('TNotebook', background=theme['bg'])
        self.style.configure(
            'TNotebook.Tab',
            background=theme['tab_bg'],
            foreground=theme['fg'])

        # Force update
        self.root.update_idletasks()

        # Apply theme to all widgets recursively
        for widget in self.root.winfo_children():
            self._apply_theme_to_widget(widget, theme_name, theme)

        # Update current theme
        self.current_theme = theme_name
        self.theme_var.set(theme_name == 'dark')

        print(f"Theme application completed: {theme_name}")

        # Update config
        if self.config is not None:
            self.config['theme'] = theme_name

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = 'dark' if self.theme_var.get() else 'light'
        self.apply_theme(new_theme)
        return new_theme

    def _apply_theme_to_widget(self, widget, theme_name, theme):
        """
        Apply the theme to a specific widget and its children.

        Args:
            widget: The widget to apply the theme to
            theme_name (str): Theme name ('light' or 'dark')
            theme (dict): Theme colors dictionary
        """
        try:
            widget_class = widget.__class__.__name__

            # Handle ttk widgets - force using direct attribute setting
            # since style sometimes doesn't apply correctly
            if hasattr(widget, 'configure'):
                try:
                    # For ttk widgets, use direct configuration when possible
                    if widget_class.startswith('Tk'):
                        # Standard Tk widgets
                        if widget_class in ['Label', 'Message']:
                            widget.configure(
                                background=theme['bg'],
                                foreground=theme['fg']
                            )
                        elif widget_class == 'Button':
                            widget.configure(
                                background=theme['button_bg'],
                                foreground=theme['button_fg'],
                                activebackground=theme['highlight_bg'],
                                activeforeground=theme['highlight_fg']
                            )
                        elif widget_class in ['Entry', 'Text']:
                            widget.configure(
                                background=theme['entry_bg'],
                                foreground=theme['entry_fg'],
                                selectbackground=theme['select_bg'],
                                selectforeground=theme['select_fg'],
                                insertbackground=theme['fg']  # Cursor color
                            )
                        elif widget_class == 'Listbox':
                            widget.configure(
                                background=theme['entry_bg'],
                                foreground=theme['entry_fg'],
                                selectbackground=theme['select_bg'],
                                selectforeground=theme['select_fg']
                            )
                        elif widget_class in ['Frame', 'LabelFrame']:
                            widget.configure(background=theme['bg'])
                        elif widget_class == 'Canvas':
                            widget.configure(background=theme['bg'])
                        elif widget_class == 'Menu':
                            # Menus require special handling
                            widget.configure(
                                background=theme['bg'],
                                foreground=theme['fg'],
                                activebackground=theme['select_bg'],
                                activeforeground=theme['select_fg']
                            )
                    # Direct apply to statusbar if found
                    elif widget_class == 'Statusbar':
                        widget.configure(background=theme['statusbar_bg'])

                    # Special handling for specific widgets
                    if hasattr(widget, 'tag_configure') and callable(
                            widget.tag_configure):
                        # Text widget with tags
                        try:
                            widget.tag_configure(
                                "sel",
                                background=theme['select_bg'],
                                foreground=theme['select_fg']
                            )
                        except (tk.TclError, AttributeError):
                            # Skip if tag doesn't exist
                            pass
                except (tk.TclError, AttributeError) as style_error:
                    # Log the error but continue with theme application
                    print(
                        f"Style config error for {widget_class}: {style_error}"
                    )

            # Apply to all children recursively
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child, theme_name, theme)

        except tk.TclError as tcl_error:
            # Skip widgets that don't support these options
            print(f"TCL error on {widget.__class__.__name__}: {tcl_error}")
        except Exception as e:
            # Catch any other errors to avoid breaking the theme application
            print(
                f"Error applying theme to {widget.__class__.__name__}: {e}"
            )