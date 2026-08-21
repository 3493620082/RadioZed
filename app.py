import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import os
import sys
import shutil
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime


def _base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

ALLOWED_LANGUAGES = [
    "AR", "CA", "CH", "CN", "CS", "DA", "DE", "EN", "ES", "ES_CL", "ES_MX",
    "FI", "FR", "HU", "ID", "IT", "JP", "KO", "NL", "NO", "PL", "PT", "PTBR",
    "RO", "RU", "STREW", "TH", "TR", "UA",
]

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.checkOutputDir()
        self.iconbitmap('icon.ico')
        self.state('zoomed')
        self.file_path: str | None = None

        config_path = os.path.join(_base_dir(), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {'language': 'CN', 'lang_strings': {}}
        self.language = self.config.get('language', 'CN')
        self.title(self.t('app_title'))

        style = ttk.Style()
        style.configure('Navbar.TFrame', background='white')
        style.configure('Delete.TButton', foreground='red')

        self._build_navbar()
        self._build_subnavbar()
        self._build_pages()
        self.show_page('welcome')

    def t(self, key: str) -> str:
        return self.config.get('lang_strings', {}).get(self.language, {}).get(key, key)

    def _set_placeholder(self, entry: ttk.Entry, placeholder: str) -> None:
        entry._placeholder = placeholder
        entry._placeholder_active = False
        entry.configure(foreground='grey')
        entry.insert(0, placeholder)
        def on_focus_in(e: tk.Event) -> None:
            if not entry._placeholder_active:
                entry._placeholder_active = True
                entry.delete(0, tk.END)
                entry.configure(foreground='black')
        def on_focus_out(e: tk.Event) -> None:
            if entry.get().strip() == '':
                entry._placeholder_active = False
                entry.configure(foreground='grey')
                entry.insert(0, entry._placeholder)
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def _build_navbar(self) -> None:
        self.navbar = ttk.Frame(self, style='Navbar.TFrame')
        self.navbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_new = ttk.Button(self.navbar, text=self.t('new_file'),
                                   command=self.new_file)
        self.btn_new.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_open = ttk.Button(self.navbar, text=self.t('open_file'),
                                   command=self.open_file)
        self.btn_open.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_save = ttk.Button(self.navbar, text=self.t('save_file'))
        self.btn_save.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_open_folder = ttk.Button(self.navbar, text=self.t('open_folder'),
                                           command=self.open_folder)
        self.btn_open_folder.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_settings = ttk.Button(self.navbar, text=self.t('settings'),
                                        command=self.open_settings)
        self.btn_settings.pack(side=tk.LEFT, padx=2, pady=2)

    def _build_subnavbar(self) -> None:
        style = ttk.Style()
        style.configure('Subnavbar.TFrame', background='#e0e0e0')

        self.subnavbar = ttk.Frame(self, style='Subnavbar.TFrame')
        self.subnavbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_channel = ttk.Button(self.subnavbar, text=self.t('channel'),
                                         command=lambda: self.show_page('channel'),
                                         state='disabled')
        self.btn_channel.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_translate = ttk.Button(self.subnavbar, text=self.t('translate'),
                                        command=lambda: self.show_page('translate'),
                                        state='disabled')
        self.btn_translate.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_server_translate = ttk.Button(self.subnavbar, text=self.t('server_translate'),
                                               command=lambda: self.show_page('server_translate'),
                                               state='disabled')
        self.btn_server_translate.pack(side=tk.LEFT, padx=2, pady=2)

    def _build_pages(self) -> None:
        self._build_welcome_page()
        self._build_channel_page()
        self._build_translate_page()
        self._build_server_translate_page()

    def _build_welcome_page(self) -> None:
        self.page_welcome = ttk.Frame(self)
        self.label_welcome = ttk.Label(self.page_welcome, text=self.t('please_open_file_first'))
        self.label_welcome.pack(expand=True)

    def _build_channel_page(self) -> None:
        self.page_channel = ttk.Frame(self)
        self.page_channel.rowconfigure(0, weight=1)

        # --- Left panel: All Channels ---
        channel_left = ttk.Frame(self.page_channel, width=200)
        channel_left.pack(side=tk.LEFT, fill=tk.Y)
        channel_left.pack_propagate(False)

        self.label_all_channels = ttk.Label(channel_left, text=self.t('all_channels'))
        self.label_all_channels.pack(anchor=tk.W, padx=4, pady=2)

        self.channel_search_var = tk.StringVar()
        self.channel_search_entry = ttk.Entry(channel_left, textvariable=self.channel_search_var)
        self.channel_search_entry.pack(fill=tk.X, padx=4, pady=(0, 2))
        self.channel_search_entry.bind('<Return>', lambda e: self.refresh_channel_list())
        self._set_placeholder(self.channel_search_entry, self.t('search_placeholder'))

        self.channel_list = ttk.Treeview(channel_left, columns=('name',), show='headings')
        self.channel_list.heading('name', text=self.t('channel_name'))
        self.channel_list.column('name', width=180)
        self.channel_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.channel_list.bind('<<TreeviewSelect>>', lambda e: self.refresh_broadcast_list())
        self.channel_list.bind('<Double-1>', lambda e: self.edit_channel())

        self.ch_context = tk.Menu(self.channel_list, tearoff=0)
        self.ch_context.add_command(label=self.t('edit'), command=self.edit_channel)
        def on_ch_right_click(event: tk.Event) -> None:
            item = self.channel_list.identify_row(event.y)
            if item:
                self.channel_list.selection_set(item)
                self.ch_context.tk_popup(event.x_root, event.y_root)
        self.channel_list.bind('<Button-3>', on_ch_right_click)

        btn_frame_left = ttk.Frame(channel_left)
        btn_frame_left.pack(side=tk.BOTTOM, anchor=tk.W, padx=2, pady=2)
        self.btn_add_channel = ttk.Button(btn_frame_left, text=self.t('add_channel'),
                   command=self.add_channel)
        self.btn_add_channel.pack(side=tk.LEFT)
        self.btn_delete_channel = ttk.Button(btn_frame_left, text=self.t('delete_channel'),
                   style='Delete.TButton', command=self.delete_channel)
        self.btn_delete_channel.pack(side=tk.LEFT, padx=(2, 0))

        # --- Middle panel: All Broadcasts ---
        channel_right = ttk.Frame(self.page_channel, width=200)
        channel_right.pack(side=tk.LEFT, fill=tk.Y)
        channel_right.pack_propagate(False)
        channel_right.columnconfigure(1, weight=1)
        channel_right.rowconfigure(2, weight=1)

        self.label_all_broadcasts = ttk.Label(channel_right, text=self.t('all_broadcasts'))
        self.label_all_broadcasts.grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)

        self.broadcast_search_var = tk.StringVar()
        self.broadcast_search_entry = ttk.Entry(channel_right, textvariable=self.broadcast_search_var)
        self.broadcast_search_entry.grid(row=1, column=0, columnspan=3, sticky='ew', padx=4, pady=(0, 2))
        self.broadcast_search_entry.bind('<Return>', lambda e: self.refresh_broadcast_list())
        self._set_placeholder(self.broadcast_search_entry, self.t('search_placeholder'))

        self.broadcast_list = ttk.Treeview(channel_right, columns=('time',), show='headings')
        self.broadcast_list.heading('time', text=self.t('broadcast'))
        self.broadcast_list.column('time', width=180)
        self.broadcast_list.grid(row=2, column=0, columnspan=3, sticky='nsew', padx=2, pady=2)
        self.broadcast_list.bind('<<TreeviewSelect>>', lambda e: self.refresh_line_list())
        self.broadcast_list.bind('<Double-1>', lambda e: self.edit_broadcast())

        self.bcast_context = tk.Menu(self.broadcast_list, tearoff=0)
        self.bcast_context.add_command(label=self.t('edit'), command=self.edit_broadcast)
        def on_bcast_right_click(event: tk.Event) -> None:
            item = self.broadcast_list.identify_row(event.y)
            if item:
                self.broadcast_list.selection_set(item)
                self.bcast_context.tk_popup(event.x_root, event.y_root)
        self.broadcast_list.bind('<Button-3>', on_bcast_right_click)

        btn_frame_bcast = ttk.Frame(channel_right)
        btn_frame_bcast.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=2, pady=2)
        self.btn_add_broadcast = ttk.Button(btn_frame_bcast, text=self.t('add_broadcast'),
                   command=self.add_broadcast)
        self.btn_add_broadcast.pack(side=tk.LEFT)
        self.btn_batch_broadcast = ttk.Button(btn_frame_bcast, text=self.t('batch_add_broadcast'),
                   command=self.batch_add_broadcasts)
        self.btn_batch_broadcast.pack(side=tk.LEFT, padx=(2, 0))
        self.btn_delete_broadcast = ttk.Button(btn_frame_bcast, text=self.t('delete_broadcast'),
                   style='Delete.TButton', command=self.delete_broadcast)
        self.btn_delete_broadcast.pack(side=tk.LEFT, padx=(2, 0))

        # --- Right panel: All Lines ---
        channel_lines = ttk.Frame(self.page_channel)
        channel_lines.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        channel_lines.columnconfigure(0, weight=1)
        channel_lines.rowconfigure(2, weight=1)

        self.label_all_lines = ttk.Label(channel_lines, text=self.t('all_lines'))
        self.label_all_lines.grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)

        self.line_search_var = tk.StringVar()
        self.line_search_entry = ttk.Entry(channel_lines, textvariable=self.line_search_var)
        self.line_search_entry.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 2))
        self.line_search_entry.bind('<Return>', lambda e: self.refresh_line_list())
        self._set_placeholder(self.line_search_entry, self.t('search_placeholder'))

        self.line_list = ttk.Treeview(channel_lines, columns=('text', 'color', 'id'), show='headings')
        self.line_list.heading('text', text=self.t('line'))
        self.line_list.heading('color', text=self.t('color'))
        self.line_list.heading('id', text=self.t('id'))
        self.line_list.column('text', width=200)
        self.line_list.column('color', width=80)
        self.line_list.column('id', width=200)
        self.line_list.grid(row=2, column=0, sticky='nsew', padx=2, pady=2)

        self.line_context = tk.Menu(self.line_list, tearoff=0)
        self.line_context.add_command(label=self.t('copy_line'), command=lambda: self._copy_line_cell('text'))
        self.line_context.add_command(label=self.t('copy_color'), command=lambda: self._copy_line_cell('color'))
        self.line_context.add_command(label=self.t('copy_id'), command=lambda: self._copy_line_cell('id'))
        self.line_context.add_separator()
        self.line_context.add_command(label=self.t('edit'), command=self.edit_line)

        def on_right_click(event: tk.Event) -> None:
            item = self.line_list.identify_row(event.y)
            if item:
                self.line_list.selection_set(item)
                self.line_context.tk_popup(event.x_root, event.y_root)

        self.line_list.bind('<Button-3>', on_right_click)
        self.line_list.bind('<Double-1>', lambda e: self.edit_line())

        btn_frame_lines = ttk.Frame(channel_lines)
        btn_frame_lines.grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)
        self.btn_add_line = ttk.Button(btn_frame_lines, text=self.t('add_line'),
                   command=self.add_line)
        self.btn_add_line.pack(side=tk.LEFT)
        self.btn_edit_line = ttk.Button(btn_frame_lines, text=self.t('edit_line'),
                   command=self.edit_line)
        self.btn_edit_line.pack(side=tk.LEFT, padx=(2, 0))
        self.btn_delete_line = ttk.Button(btn_frame_lines, text=self.t('delete_line'),
                   style='Delete.TButton', command=self.delete_line)
        self.btn_delete_line.pack(side=tk.LEFT, padx=(2, 0))
        self.btn_batch_line = ttk.Button(btn_frame_lines, text=self.t('batch_add_line'),
                   command=self.batch_add_lines)
        self.btn_batch_line.pack(side=tk.LEFT, padx=(2, 0))
        self.btn_copy_line = ttk.Button(btn_frame_lines, text=self.t('copy_line_data'),
                   command=self.copy_line_data)
        self.btn_copy_line.pack(side=tk.LEFT, padx=(2, 0))
        self.btn_paste_line = ttk.Button(btn_frame_lines, text=self.t('paste_line_data'),
                   command=self.paste_line_data)
        self.btn_paste_line.pack(side=tk.LEFT, padx=(2, 0))

    def _build_translate_page(self) -> None:
        self.page_translate = ttk.Frame(self)
        self.page_translate.rowconfigure(0, weight=1)
        self.page_translate.columnconfigure(1, weight=1)

        translate_left = ttk.Frame(self.page_translate, width=200)
        translate_left.pack(side=tk.LEFT, fill=tk.Y)
        translate_left.pack_propagate(False)

        self.label_all_languages = ttk.Label(translate_left, text=self.t('all_languages'))
        self.label_all_languages.pack(anchor=tk.W, padx=4, pady=2)

        self.lang_list = ttk.Treeview(translate_left, columns=('lang',), show='headings')
        self.lang_list.heading('lang', text=self.t('language'))
        self.lang_list.column('lang', width=180)
        self.lang_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=2, pady=2)

        btn_frame_lang = ttk.Frame(translate_left)
        btn_frame_lang.pack(side=tk.BOTTOM, anchor=tk.W, padx=2, pady=2)
        self.btn_add_language = ttk.Button(btn_frame_lang, text=self.t('add_language'),
                   command=self.add_language)
        self.btn_add_language.pack(side=tk.LEFT)
        self.btn_delete_language = ttk.Button(btn_frame_lang, text=self.t('delete_language'),
                   style='Delete.TButton', command=self.delete_language)
        self.btn_delete_language.pack(side=tk.LEFT, padx=(2, 0))

        translate_right = ttk.Frame(self.page_translate)
        translate_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        translate_right.rowconfigure(2, weight=1)
        translate_right.columnconfigure(0, weight=1)

        self.label_all_texts = ttk.Label(translate_right, text=self.t('all_texts'))
        self.label_all_texts.grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)

        self.translate_search_var = tk.StringVar()
        self.translate_search_entry = ttk.Entry(translate_right, textvariable=self.translate_search_var)
        self.translate_search_entry.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 2))
        self.translate_search_entry.bind('<Return>', lambda e: self._load_translate_data())
        self._set_placeholder(self.translate_search_entry, self.t('search_placeholder'))

        self.translate_tree = ttk.Treeview(translate_right, columns=('key', 'val'), show='headings')
        self.translate_tree.heading('key', text=self.t('id'))
        self.translate_tree.heading('val', text=self.t('text'))
        self.translate_tree.column('key', width=300)
        self.translate_tree.column('val', width=400)
        self.translate_tree.grid(row=2, column=0, sticky='nsew', padx=2, pady=2)
        self.translate_tree.bind('<Double-1>', self._edit_translate_entry)

        self.btn_edit_text = ttk.Button(translate_right, text=self.t('edit_text'),
                   command=self._edit_translate_entry)
        self.btn_edit_text.grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)

        self.lang_list.bind('<<TreeviewSelect>>', lambda e: self._load_translate_data())

        self.lang_context = tk.Menu(self.lang_list, tearoff=0)
        self.lang_context.add_command(label=self.t('open_file_location'),
                                      command=self._open_lang_folder)
        self.lang_list.bind('<Button-3>', self._on_lang_right_click)

    def _build_server_translate_page(self) -> None:
        self.page_server_translate = ttk.Frame(self)
        self.page_server_translate.rowconfigure(0, weight=1)
        self.page_server_translate.columnconfigure(1, weight=1)

        st_left = ttk.Frame(self.page_server_translate, width=200)
        st_left.pack(side=tk.LEFT, fill=tk.Y)
        st_left.pack_propagate(False)

        self.label_st_all_languages = ttk.Label(st_left, text=self.t('all_languages'))
        self.label_st_all_languages.pack(anchor=tk.W, padx=4, pady=2)

        self.st_lang_list = ttk.Treeview(st_left, columns=('lang',), show='headings')
        self.st_lang_list.heading('lang', text=self.t('language'))
        self.st_lang_list.column('lang', width=180)
        self.st_lang_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.label_st_only_cn_en = ttk.Button(st_left, text=self.t('st_only_cn_en'),
                                               state='disabled')
        self.label_st_only_cn_en.pack(side=tk.BOTTOM, anchor=tk.W, padx=2, pady=2)

        st_right = ttk.Frame(self.page_server_translate)
        st_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        st_right.rowconfigure(2, weight=1)
        st_right.columnconfigure(0, weight=1)

        self.label_st_all_texts = ttk.Label(st_right, text=self.t('all_texts'))
        self.label_st_all_texts.grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)

        self.st_search_var = tk.StringVar()
        self.st_search_entry = ttk.Entry(st_right, textvariable=self.st_search_var)
        self.st_search_entry.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 2))
        self.st_search_entry.bind('<Return>', lambda e: self._load_st_translate_data())
        self._set_placeholder(self.st_search_entry, self.t('search_placeholder'))

        self.st_translate_tree = ttk.Treeview(st_right, columns=('key', 'val'), show='headings')
        self.st_translate_tree.heading('key', text=self.t('id'))
        self.st_translate_tree.heading('val', text=self.t('text'))
        self.st_translate_tree.column('key', width=300)
        self.st_translate_tree.column('val', width=400)
        self.st_translate_tree.grid(row=2, column=0, sticky='nsew', padx=2, pady=2)

        btn_frame_st = ttk.Frame(st_right)
        btn_frame_st.grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)
        self.btn_st_edit_text = ttk.Button(btn_frame_st, text=self.t('sync_current_lang'),
                   command=self._sync_st_language)
        self.btn_st_edit_text.pack(side=tk.LEFT)
        self.btn_st_open_folder = ttk.Button(btn_frame_st, text=self.t('open_file_location'),
                   command=self._open_st_lang_folder)
        self.btn_st_open_folder.pack(side=tk.LEFT, padx=(2, 0))

        self.st_lang_list.bind('<<TreeviewSelect>>', lambda e: self._load_st_translate_data())

    def refresh_ui_text(self) -> None:
        t = self.t
        self.title(t('app_title'))
        # Navbar
        self.btn_new.config(text=t('new_file'))
        self.btn_open.config(text=t('open_file'))
        self.btn_save.config(text=t('save_file'))
        self.btn_open_folder.config(text=t('open_folder'))
        self.btn_settings.config(text=t('settings'))
        # Subnavbar
        self.btn_channel.config(text=t('channel'))
        self.btn_translate.config(text=t('translate'))
        self.btn_server_translate.config(text=t('server_translate'))
        # Welcome
        self.label_welcome.config(text=t('please_open_file_first'))
        # Channel page
        self.label_all_channels.config(text=t('all_channels'))
        self.channel_list.heading('name', text=t('channel_name'))
        self.btn_add_channel.config(text=t('add_channel'))
        self.btn_delete_channel.config(text=t('delete_channel'))
        self.label_all_broadcasts.config(text=t('all_broadcasts'))
        self.broadcast_list.heading('time', text=t('broadcast'))
        self.btn_add_broadcast.config(text=t('add_broadcast'))
        self.btn_delete_broadcast.config(text=t('delete_broadcast'))
        self.btn_batch_broadcast.config(text=t('batch_add_broadcast'))
        self.label_all_lines.config(text=t('all_lines'))
        self.line_list.heading('text', text=t('line'))
        self.line_list.heading('color', text=t('color'))
        self.line_list.heading('id', text=t('id'))
        self.btn_add_line.config(text=t('add_line'))
        self.btn_edit_line.config(text=t('edit_line'))
        self.btn_delete_line.config(text=t('delete_line'))
        self.btn_batch_line.config(text=t('batch_add_line'))
        self.btn_copy_line.config(text=t('copy_line_data'))
        self.btn_paste_line.config(text=t('paste_line_data'))
        # Context menus
        self.ch_context.entryconfigure(0, label=t('edit'))
        self.bcast_context.entryconfigure(0, label=t('edit'))
        self.line_context.entryconfigure(0, label=t('copy_line'))
        self.line_context.entryconfigure(1, label=t('copy_color'))
        self.line_context.entryconfigure(2, label=t('copy_id'))
        self.line_context.entryconfigure(4, label=t('edit'))
        # Translate page
        self.label_all_languages.config(text=t('all_languages'))
        self.lang_list.heading('lang', text=t('language'))
        self.btn_add_language.config(text=t('add_language'))
        self.btn_delete_language.config(text=t('delete_language'))
        self.label_all_texts.config(text=t('all_texts'))
        self.translate_tree.heading('key', text=t('id'))
        self.translate_tree.heading('val', text=t('text'))
        self.btn_edit_text.config(text=t('edit_text'))
        self.lang_context.entryconfigure(0, label=t('open_file_location'))
        # Server translate page
        self.label_st_all_languages.config(text=t('all_languages'))
        self.st_lang_list.heading('lang', text=t('language'))
        self.label_st_all_texts.config(text=t('all_texts'))
        self.st_translate_tree.heading('key', text=t('id'))
        self.st_translate_tree.heading('val', text=t('text'))
        self.btn_st_edit_text.config(text=t('sync_current_lang'))
        self.btn_st_open_folder.config(text=t('open_file_location'))
        self.label_st_only_cn_en.config(text=t('st_only_cn_en'))
        # Search placeholders
        for entry_attr in ('channel_search_entry', 'broadcast_search_entry',
                           'line_search_entry', 'translate_search_entry',
                           'st_search_entry'):
            entry = getattr(self, entry_attr, None)
            if entry is not None and hasattr(entry, '_placeholder'):
                entry._placeholder = t('search_placeholder')
                if not entry._placeholder_active:
                    entry.delete(0, tk.END)
                    entry.insert(0, entry._placeholder)
        # Update title if file is open
        if self.file_path:
            self.update_title()

    def new_file(self) -> None:
        current_dir = _base_dir()
        output_dir = os.path.join(current_dir, 'output')
        folder_name = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_dir = os.path.join(output_dir, folder_name)
        os.makedirs(project_dir, exist_ok=True)

        xml_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<RadioData>
  <!-- 1. 根标签 -->
  <RootInfo>
    <SourceFile>Radio</SourceFile>
    <FileGUID>{uuid.uuid4()}</FileGUID>
    <Version>1</Version>
  </RootInfo>
  <Channels>
    
  </Channels>
</RadioData>
"""
        xml_path = os.path.join(project_dir, 'RadioData.xml')
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        translate_dir = os.path.join(project_dir, 'Translate')
        cn_dir = os.path.join(translate_dir, 'CN')
        en_dir = os.path.join(translate_dir, 'EN')
        os.makedirs(cn_dir, exist_ok=True)
        os.makedirs(en_dir, exist_ok=True)
        for lang_dir in (cn_dir, en_dir):
            json_path = os.path.join(lang_dir, 'RadioData.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write('{}')

        # Create ServerTranslate folder and copy src translation files
        st_dir = os.path.join(project_dir, 'ServerTranslate')
        st_cn_dir = os.path.join(st_dir, 'CN')
        st_en_dir = os.path.join(st_dir, 'EN')
        os.makedirs(st_cn_dir, exist_ok=True)
        os.makedirs(st_en_dir, exist_ok=True)
        src_dir = os.path.join(_base_dir(), 'src')
        st_src_map = {
            st_cn_dir: 'Server_RadioData_CN.json',
            st_en_dir: 'Server_RadioData_EN.json',
        }
        for dst_dir, src_filename in st_src_map.items():
            src_path = os.path.join(src_dir, src_filename)
            dst_path = os.path.join(dst_dir, 'RadioData.json')
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

        self.file_path = xml_path
        self.btn_channel.config(state='normal')
        self.btn_translate.config(state='normal')
        self.btn_server_translate.config(state='normal')
        self.update_title()
        self.refresh_channel_list()
        self.show_page('channel')

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t('select_file'),
            filetypes=[(self.t('xml_files'), "*.xml")]
        )
        if path:
            self.file_path = path
            self.btn_channel.config(state='normal')
            self.btn_translate.config(state='normal')
            self.btn_server_translate.config(state='normal')
            self.update_title()
            self.refresh_channel_list()
            self.show_page('channel')

    def update_title(self) -> None:
        current_dir = _base_dir()
        rel_path = os.path.relpath(self.file_path, current_dir)
        self.title(f"{self.t('app_title')} - {rel_path}")

    def open_folder(self) -> None:
        if self.file_path:
            folder = os.path.dirname(os.path.abspath(self.file_path))
            os.startfile(folder)

    def open_settings(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title(self.t('settings_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('language_label')).pack(anchor=tk.W)
        lang_var = tk.StringVar(value=self.language)
        lang_combo = ttk.Combobox(frame, textvariable=lang_var,
                                  values=["CN", "EN"], state="readonly", width=20)
        lang_combo.pack(fill=tk.X, pady=(2, 8))

        version = self.config.get('version', '')
        ttk.Label(frame, text=self.t('version_label')).pack(anchor=tk.W)
        ttk.Label(frame, text=f'v{version}').pack(anchor=tk.W, pady=(2, 8))

        def on_confirm() -> None:
            lang = lang_var.get()
            self.language = lang
            self.config['language'] = lang
            config_path = os.path.join(_base_dir(), 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.refresh_ui_text()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def refresh_channel_list(self) -> None:
        for item in self.channel_list.get_children():
            self.channel_list.delete(item)
        for item in self.broadcast_list.get_children():
            self.broadcast_list.delete(item)
        for item in self.line_list.get_children():
            self.line_list.delete(item)
        if not self.file_path:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is not None:
            search = self.channel_search_var.get().strip().lower()
            if getattr(self.channel_search_entry, '_placeholder_active', True) is False:
                search = ''
            for i, ch in enumerate(channels.findall('ChannelEntry')):
                name = ch.get('name', '')
                cat = ch.get('cat', '')
                cat_display = self.t('radio') if cat == 'Radio' else self.t('television')
                display = f"{cat_display} - {name}"
                if name and (not search or search in display.lower()):
                    self.channel_list.insert('', tk.END, iid=str(i), values=(display,))

    def refresh_broadcast_list(self) -> None:
        for item in self.broadcast_list.get_children():
            self.broadcast_list.delete(item)
        for item in self.line_list.get_children():
            self.line_list.delete(item)
        ch_index = self._get_tree_index(self.channel_list)
        if ch_index is None or not self.file_path:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        ch_entry = ch_entries[ch_index]
        script = ch_entry.find('ScriptEntry')
        if script is None:
            return
        for i, bcast in enumerate(script.findall('BroadcastEntry')):
            ts = int(bcast.get('timestamp', '0'))
            es = int(bcast.get('endstamp', '0'))
            ts_day = ts // 1440
            ts_min = ts % 1440
            es_day = es // 1440
            es_min = es % 1440
            ts_str = f"{ts_min // 60}:{ts_min % 60:02d}"
            es_str = f"{es_min // 60}:{es_min % 60:02d}"
            display = f"Day {ts_day}  {ts_str} - {es_str}"
            search = self.broadcast_search_var.get().strip().lower()
            if getattr(self.broadcast_search_entry, '_placeholder_active', True) is False:
                search = ''
            if not search or search in display.lower():
                self.broadcast_list.insert('', tk.END, iid=str(i), values=(display,))

    def _get_selected_bcast(self) -> ET.Element | None:
        ch_index = self._get_tree_index(self.channel_list)
        b_index = self._get_tree_index(self.broadcast_list)
        if ch_index is None or b_index is None or not self.file_path:
            return None
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return None
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return None
        script = ch_entries[ch_index].find('ScriptEntry')
        if script is None:
            return None
        bcasts = script.findall('BroadcastEntry')
        if b_index >= len(bcasts):
            return None
        return bcasts[b_index]

    def refresh_line_list(self) -> None:
        for item in self.line_list.get_children():
            self.line_list.delete(item)
        bcast = self._get_selected_bcast()
        if bcast is None:
            return

        project_dir = os.path.dirname(self.file_path)
        json_path = os.path.join(project_dir, 'Translate', self.language, 'RadioData.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cn_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cn_data = {}

        for i, line in enumerate(bcast.findall('LineEntry')):
            r = int(line.get('r', '255'))
            g = int(line.get('g', '192'))
            b = int(line.get('b', '0'))
            line_id = line.get('ID', '')
            text = cn_data.get(f'RD_{line_id}', '')
            color_str = f'{r}, {g}, {b}'
            search = self.line_search_var.get().strip().lower()
            if getattr(self.line_search_entry, '_placeholder_active', True) is False:
                search = ''
            if search and search not in text.lower() and search not in color_str.lower() and search not in line_id.lower():
                continue
            tag = f'color_{r}_{g}_{b}'
            self.line_list.tag_configure(tag, foreground=f'#{r:02x}{g:02x}{b:02x}')
            self.line_list.insert('', tk.END, iid=str(i), values=(text, color_str, line_id), tags=(tag,))

    def add_line(self) -> None:
        bcast = self._get_selected_bcast()
        if bcast is None:
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t('add_line_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('line_text_label')).pack(anchor=tk.W)
        text_var = tk.StringVar()
        ttk.Entry(frame, textvariable=text_var, width=50).pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('color_label')).pack(anchor=tk.W)
        color = {'r': 255, 'g': 192, 'b': 0}

        color_frame = ttk.Frame(frame)
        color_frame.pack(fill=tk.X, pady=(2, 8))

        def update_from_rgb(*args) -> None:
            try:
                parts = rgb_var.get().strip().split(',')
                if len(parts) == 3:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        color['r'], color['g'], color['b'] = r, g, b
                        color_btn.config(bg=f'#{r:02x}{g:02x}{b:02x}')
            except ValueError:
                pass

        def update_rgb_entry() -> None:
            rgb_var.set(f"{color['r']}, {color['g']}, {color['b']}")

        rgb_var = tk.StringVar(value="255, 192, 0")
        rgb_var.trace('w', update_from_rgb)
        ttk.Entry(color_frame, textvariable=rgb_var, width=20).pack(side=tk.LEFT)

        def pick_color() -> None:
            rgb, hex_color = colorchooser.askcolor(
                f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}',
                title=self.t('select_color')
            )
            if rgb:
                color['r'], color['g'], color['b'] = int(rgb[0]), int(rgb[1]), int(rgb[2])
                color_btn.config(bg=f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}')
                update_rgb_entry()

        color_btn = tk.Button(color_frame, text='', width=6, command=pick_color,
                              bg='#ffc000', relief=tk.RAISED)
        color_btn.pack(side=tk.LEFT, padx=(4, 0))

        def on_confirm() -> None:
            text = text_var.get().strip()
            if not text:
                return

            tree = ET.parse(self.file_path)
            root = tree.getroot()
            channels = root.find('Channels')
            if channels is None:
                return
            ch_index = self._get_tree_index(self.channel_list)
            b_index = self._get_tree_index(self.broadcast_list)
            if ch_index is None or b_index is None:
                return
            ch_entries = channels.findall('ChannelEntry')
            if ch_index >= len(ch_entries):
                return
            script = ch_entries[ch_index].find('ScriptEntry')
            if script is None:
                return
            bcasts = script.findall('BroadcastEntry')
            if b_index >= len(bcasts):
                return
            bcast = bcasts[b_index]

            line_id = str(uuid.uuid4())
            ET.SubElement(bcast, 'LineEntry', {
                'ID': line_id,
                'r': str(color['r']),
                'g': str(color['g']),
                'b': str(color['b']),
            })

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)

            self._sync_translate_all(line_id, text)

            self.refresh_line_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def batch_add_lines(self) -> None:
        bcast = self._get_selected_bcast()
        if bcast is None:
            messagebox.showwarning(self.t('warning'), self.t('no_bcast_selected'))
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t('batch_add_line_title'))
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        lines_data = []

        def select_file() -> None:
            path = filedialog.askopenfilename(
                filetypes=[(self.t('batch_select_file'), '*.txt')]
            )
            if not path:
                return
            file_label.config(text=path)
            lines_data.clear()
            for item in preview_tree.get_children():
                preview_tree.delete(item)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            lines_data.append(text)
                            preview_tree.insert('', tk.END, values=(text,))
            except Exception as e:
                messagebox.showerror(self.t('error'), str(e))

        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(file_frame, text=self.t('batch_select_file'),
                   command=select_file).pack(side=tk.LEFT)
        file_label = ttk.Label(file_frame, text='', foreground='gray')
        file_label.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(frame, text=self.t('batch_preview_label')).pack(anchor=tk.W)
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 8))
        preview_tree = ttk.Treeview(tree_frame, columns=('line',), show='headings', height=12)
        preview_tree.heading('line', text=self.t('batch_line_col'))
        preview_tree.column('line', width=400)
        preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def on_confirm() -> None:
            if not lines_data:
                return
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            channels = root.find('Channels')
            ch_index = self._get_tree_index(self.channel_list)
            b_index = self._get_tree_index(self.broadcast_list)
            if channels is None or ch_index is None or b_index is None:
                return
            ch_entries = channels.findall('ChannelEntry')
            if ch_index >= len(ch_entries):
                return
            script = ch_entries[ch_index].find('ScriptEntry')
            if script is None:
                return
            bcasts = script.findall('BroadcastEntry')
            if b_index >= len(bcasts):
                return
            bcast = bcasts[b_index]

            for text in lines_data:
                line_id = str(uuid.uuid4())
                ET.SubElement(bcast, 'LineEntry', {
                    'ID': line_id,
                    'r': '255',
                    'g': '192',
                    'b': '0',
                })
                self._sync_translate_all(line_id, text)

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_line_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def _sync_translate_all(self, line_id: str, text: str) -> None:
        project_dir = os.path.dirname(self.file_path)
        translate_dir = os.path.join(project_dir, 'Translate')
        if not os.path.isdir(translate_dir):
            return
        for lang_dir in os.listdir(translate_dir):
            json_path = os.path.join(translate_dir, lang_dir, 'RadioData.json')
            if os.path.isfile(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = {}
                data[f'RD_{line_id}'] = text
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

    def _get_selected_line(self) -> ET.Element | None:
        bcast = self._get_selected_bcast()
        if bcast is None:
            return None
        l_index = self._get_tree_index(self.line_list)
        if l_index is None:
            return None
        lines = bcast.findall('LineEntry')
        if l_index >= len(lines):
            return None
        return lines[l_index]

    def delete_channel(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        if ch_index is None or not self.file_path:
            return
        if not messagebox.askyesno(self.t('confirm_delete'), self.t('confirm_delete_channel')):
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        channels.remove(ch_entries[ch_index])
        ET.indent(tree, space='  ')
        tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
        self.refresh_channel_list()

    def delete_broadcast(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        b_index = self._get_tree_index(self.broadcast_list)
        if ch_index is None or b_index is None or not self.file_path:
            return
        if not messagebox.askyesno(self.t('confirm_delete'), self.t('confirm_delete_broadcast')):
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        script = ch_entries[ch_index].find('ScriptEntry')
        if script is None:
            return
        bcasts = script.findall('BroadcastEntry')
        if b_index >= len(bcasts):
            return
        script.remove(bcasts[b_index])
        ET.indent(tree, space='  ')
        tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
        self.refresh_broadcast_list()

    def delete_line(self) -> None:
        if not self.line_list.selection():
            return
        if not messagebox.askyesno(self.t('confirm_delete'), self.t('confirm_delete_line')):
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_index = self._get_tree_index(self.channel_list)
        b_index = self._get_tree_index(self.broadcast_list)
        if ch_index is None or b_index is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        script = ch_entries[ch_index].find('ScriptEntry')
        if script is None:
            return
        bcasts = script.findall('BroadcastEntry')
        if b_index >= len(bcasts):
            return
        lines = bcasts[b_index].findall('LineEntry')
        line_sel = self.line_list.selection()
        if not line_sel:
            return
        try:
            line_idx = int(line_sel[0])
        except (ValueError, TypeError):
            return
        if line_idx >= len(lines):
            return
        line_id = lines[line_idx].get('ID', '')
        bcasts[b_index].remove(lines[line_idx])
        ET.indent(tree, space='  ')
        tree.write(self.file_path, encoding='utf-8', xml_declaration=True)

        # Remove translation key from all language files
        if line_id:
            project_dir = os.path.dirname(self.file_path)
            translate_dir = os.path.join(project_dir, 'Translate')
            if os.path.isdir(translate_dir):
                for lang in os.listdir(translate_dir):
                    jp = os.path.join(translate_dir, lang, 'RadioData.json')
                    if not os.path.isfile(jp):
                        continue
                    try:
                        with open(jp, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        continue
                    data.pop(f'RD_{line_id}', None)
                    with open(jp, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

        self.refresh_line_list()

    def _copy_line_cell(self, column: str) -> None:
        sel = self.line_list.selection()
        if not sel:
            return
        values = self.line_list.item(sel[0], 'values')
        col_map = {'text': 0, 'color': 1, 'id': 2}
        idx = col_map.get(column, 0)
        if idx < len(values):
            self.clipboard_clear()
            self.clipboard_append(values[idx])

    def copy_line_data(self) -> None:
        sel = self.line_list.selection()
        if not sel:
            messagebox.showwarning(self.t('warning'), self.t('no_line_selected'))
            return
        items = []
        for iid in sel:
            values = self.line_list.item(iid, 'values')
            if len(values) < 2:
                continue
            text = values[0]
            color_str = values[1]
            parts = color_str.split(',')
            r = int(parts[0].strip()) if len(parts) > 0 else 255
            g = int(parts[1].strip()) if len(parts) > 1 else 192
            b = int(parts[2].strip()) if len(parts) > 2 else 0
            items.append({'text': text, 'r': r, 'g': g, 'b': b})
        self.clipboard_clear()
        self.clipboard_append(str(items))

    def paste_line_data(self) -> None:
        if not self.file_path:
            return
        bcast = self._get_selected_bcast()
        if bcast is None:
            return
        try:
            clip_text = self.clipboard_get()
        except Exception:
            return
        if not clip_text:
            return
        try:
            data = eval(clip_text)
        except Exception:
            return
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            return

        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_index = self._get_tree_index(self.channel_list)
        b_index = self._get_tree_index(self.broadcast_list)
        if ch_index is None or b_index is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        script = ch_entries[ch_index].find('ScriptEntry')
        if script is None:
            return
        bcasts = script.findall('BroadcastEntry')
        if b_index >= len(bcasts):
            return
        bcast_el = bcasts[b_index]

        for item in items:
            if not isinstance(item, dict):
                continue
            text = item.get('text', '')
            r = item.get('r', 255)
            g = item.get('g', 192)
            b = item.get('b', 0)
            if not text:
                continue
            line_id = str(uuid.uuid4())
            ET.SubElement(bcast_el, 'LineEntry', {
                'ID': line_id,
                'r': str(r),
                'g': str(g),
                'b': str(b),
            })
            self._sync_translate_all(line_id, text)

        ET.indent(tree, space='  ')
        tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
        self.refresh_line_list()

    def edit_line(self) -> None:
        line_entry = self._get_selected_line()
        if line_entry is None:
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t('edit_line_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('line_text_label')).pack(anchor=tk.W)
        line_id = line_entry.get('ID', '')
        project_dir = os.path.dirname(self.file_path)
        json_path = os.path.join(project_dir, 'Translate', self.language, 'RadioData.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cn_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cn_data = {}
        text_var = tk.StringVar(value=cn_data.get(f'RD_{line_id}', ''))
        ttk.Entry(frame, textvariable=text_var, width=50).pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('color_label')).pack(anchor=tk.W)
        color = {
            'r': int(line_entry.get('r', '255')),
            'g': int(line_entry.get('g', '192')),
            'b': int(line_entry.get('b', '0')),
        }

        color_frame = ttk.Frame(frame)
        color_frame.pack(fill=tk.X, pady=(2, 8))

        def update_from_rgb(*args) -> None:
            try:
                parts = rgb_var.get().strip().split(',')
                if len(parts) == 3:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        color['r'], color['g'], color['b'] = r, g, b
                        color_btn.config(bg=f'#{r:02x}{g:02x}{b:02x}')
            except ValueError:
                pass

        def update_rgb_entry() -> None:
            rgb_var.set(f"{color['r']}, {color['g']}, {color['b']}")

        rgb_var = tk.StringVar(value=f"{color['r']}, {color['g']}, {color['b']}")
        rgb_var.trace('w', update_from_rgb)
        ttk.Entry(color_frame, textvariable=rgb_var, width=20).pack(side=tk.LEFT)

        def pick_color() -> None:
            rgb, hex_color = colorchooser.askcolor(
                f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}',
                title=self.t('select_color')
            )
            if rgb:
                color['r'], color['g'], color['b'] = int(rgb[0]), int(rgb[1]), int(rgb[2])
                color_btn.config(bg=f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}')
                update_rgb_entry()

        color_btn = tk.Button(color_frame, text='', width=6, command=pick_color,
                              bg=f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}',
                              relief=tk.RAISED)
        color_btn.pack(side=tk.LEFT, padx=(4, 0))

        def on_confirm() -> None:
            text = text_var.get().strip()
            if not text:
                return

            tree = ET.parse(self.file_path)
            root = tree.getroot()
            channels = root.find('Channels')
            ch_index = self._get_tree_index(self.channel_list)
            b_index = self._get_tree_index(self.broadcast_list)
            l_index = self._get_tree_index(self.line_list)
            if channels is None or ch_index is None or b_index is None or l_index is None:
                return
            ch_entries = channels.findall('ChannelEntry')
            if ch_index >= len(ch_entries):
                return
            script = ch_entries[ch_index].find('ScriptEntry')
            if script is None:
                return
            bcasts = script.findall('BroadcastEntry')
            if b_index >= len(bcasts):
                return
            line_entries = bcasts[b_index].findall('LineEntry')
            if l_index >= len(line_entries):
                return
            le = line_entries[l_index]
            le.set('r', str(color['r']))
            le.set('g', str(color['g']))
            le.set('b', str(color['b']))

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)

            translate_dir = os.path.join(project_dir, 'Translate')
            if os.path.isdir(translate_dir):
                for lang in os.listdir(translate_dir):
                    jp = os.path.join(translate_dir, lang, 'RadioData.json')
                    if not os.path.isfile(jp):
                        continue
                    try:
                        with open(jp, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        data = {}
                    data[f'RD_{line_id}'] = text
                    with open(jp, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

            self.refresh_line_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def add_broadcast(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        if ch_index is None:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        ch_entry = ch_entries[ch_index]
        script = ch_entry.find('ScriptEntry')
        if script is None:
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t('add_broadcast_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('start_time')).grid(row=0, column=0, sticky=tk.W, pady=4)
        time_values = [f"{h}:00" for h in range(0, 25)]
        time_var = tk.StringVar(value="0:00")
        ttk.Combobox(frame, textvariable=time_var, values=time_values,
                     state="readonly", width=22).grid(row=0, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('end_time')).grid(row=1, column=0, sticky=tk.W, pady=4)
        end_var = tk.StringVar(value="6:00")
        ttk.Combobox(frame, textvariable=end_var, values=time_values,
                     state="readonly", width=22).grid(row=1, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('day')).grid(row=2, column=0, sticky=tk.W, pady=4)
        day_var = tk.StringVar(value="0")

        def validate_day(P: str) -> bool:
            if P == '':
                return True
            return P.isdigit() and int(P) >= 0
        vcmd = (dialog.register(validate_day), '%P')
        ttk.Entry(frame, textvariable=day_var, width=24,
                  validate='key', validatecommand=vcmd).grid(row=2, column=1, pady=4, padx=(8, 0))

        def on_confirm() -> None:
            day_str = day_var.get().strip()
            if not day_str:
                return
            day = int(day_str)
            h, m = map(int, time_var.get().split(':'))
            start_minutes = h * 60 + m
            eh, em = map(int, end_var.get().split(':'))
            end_minutes = eh * 60 + em
            if end_minutes <= start_minutes:
                messagebox.showwarning(self.t('notice'), self.t('end_time_before_start_time'))
                return
            timestamp = day * 1440 + start_minutes
            endstamp = day * 1440 + end_minutes

            bcast = ET.SubElement(script, 'BroadcastEntry', {
                'ID': str(uuid.uuid4()),
                'timestamp': str(timestamp),
                'endstamp': str(endstamp),
                'type': 'ActivateBroadcast',
                'day': str(day),
                'advertCat': 'none',
                'isSegment': 'false',
            })
            bcast.text = '\n'

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_broadcast_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def batch_add_broadcasts(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        if ch_index is None:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        ch_entry = ch_entries[ch_index]
        script = ch_entry.find('ScriptEntry')
        if script is None:
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t('batch_add_broadcast_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('start_day')).pack(anchor=tk.W)
        start_var = tk.StringVar(value='1')

        def validate_int(P: str) -> bool:
            if P == '':
                return True
            return P.isdigit() and int(P) >= 0
        vcmd = (dialog.register(validate_int), '%P')
        ttk.Entry(frame, textvariable=start_var, width=24,
                  validate='key', validatecommand=vcmd).pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('end_day')).pack(anchor=tk.W)
        end_var = tk.StringVar(value='1')
        ttk.Entry(frame, textvariable=end_var, width=24,
                  validate='key', validatecommand=vcmd).pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('interval_hours')).pack(anchor=tk.W)
        interval_var = tk.StringVar(value='1')
        interval_combo = ttk.Combobox(frame, textvariable=interval_var,
                                      values=['1', '2', '3', '4', '6', '8', '12'],
                                      state='readonly', width=22)
        interval_combo.pack(fill=tk.X, pady=(2, 8))

        def on_confirm() -> None:
            s_str = start_var.get().strip()
            e_str = end_var.get().strip()
            if not s_str or not e_str:
                return
            start_day = int(s_str)
            end_day = int(e_str)
            interval = int(interval_var.get())

            if start_day > end_day:
                messagebox.showwarning(self.t('notice'), self.t('start_day_gt_end_day'))
                return

            for day in range(start_day, end_day + 1):
                for hour in range(0, 24, interval):
                    timestamp = day * 1440 + hour * 60
                    endstamp = day * 1440 + (hour + interval) * 60
                    bcast = ET.SubElement(script, 'BroadcastEntry', {
                        'ID': str(uuid.uuid4()),
                        'timestamp': str(timestamp),
                        'endstamp': str(endstamp),
                        'type': 'ActivateBroadcast',
                        'day': str(day),
                        'advertCat': 'none',
                        'isSegment': 'false',
                    })
                    bcast.text = '\n'

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_broadcast_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def edit_broadcast(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        b_index = self._get_tree_index(self.broadcast_list)
        if ch_index is None or b_index is None or not self.file_path:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        script = ch_entries[ch_index].find('ScriptEntry')
        if script is None:
            return
        bcasts = script.findall('BroadcastEntry')
        if b_index >= len(bcasts):
            return
        bcast = bcasts[b_index]
        current_ts = int(bcast.get('timestamp', '0'))
        current_es = int(bcast.get('endstamp', '360'))
        current_day = current_ts // 1440
        ts_min = current_ts % 1440
        es_min = current_es % 1440
        ts_default = f"{ts_min // 60}:{ts_min % 60:02d}"
        es_default = f"{es_min // 60}:{es_min % 60:02d}"

        dialog = tk.Toplevel(self)
        dialog.title(self.t('edit_broadcast_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('start_time')).grid(row=0, column=0, sticky=tk.W, pady=4)
        time_values = [f"{h}:00" for h in range(0, 25)]
        time_var = tk.StringVar(value=ts_default)
        ttk.Combobox(frame, textvariable=time_var, values=time_values,
                     state="readonly", width=22).grid(row=0, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('end_time')).grid(row=1, column=0, sticky=tk.W, pady=4)
        end_var = tk.StringVar(value=es_default)
        ttk.Combobox(frame, textvariable=end_var, values=time_values,
                     state="readonly", width=22).grid(row=1, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('day')).grid(row=2, column=0, sticky=tk.W, pady=4)
        day_var = tk.StringVar(value=str(current_day))

        def validate_day(P: str) -> bool:
            if P == '':
                return True
            return P.isdigit() and int(P) >= 0
        vcmd = (dialog.register(validate_day), '%P')
        ttk.Entry(frame, textvariable=day_var, width=24,
                  validate='key', validatecommand=vcmd).grid(row=2, column=1, pady=4, padx=(8, 0))

        def on_confirm() -> None:
            day_str = day_var.get().strip()
            if not day_str:
                return
            day = int(day_str)
            h, m = map(int, time_var.get().split(':'))
            start_minutes = h * 60 + m
            eh, em = map(int, end_var.get().split(':'))
            end_minutes = eh * 60 + em
            if end_minutes <= start_minutes:
                messagebox.showwarning(self.t('notice'), self.t('end_time_before_start_time'))
                return
            timestamp = day * 1440 + start_minutes
            endstamp = day * 1440 + end_minutes

            bcast.set('timestamp', str(timestamp))
            bcast.set('endstamp', str(endstamp))
            bcast.set('day', str(day))

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_broadcast_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def add_channel(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title(self.t('add_channel_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('channel_name_label')).grid(row=0, column=0, sticky=tk.W, pady=4)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=24).grid(row=0, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('channel_category')).grid(row=1, column=0, sticky=tk.W, pady=4)
        cat_var = tk.StringVar(value=self.t('radio'))

        ttk.Label(frame, text=self.t('channel_frequency')).grid(row=2, column=0, sticky=tk.W, pady=4)
        freq_var = tk.StringVar(value="88.0")
        freq_combo = ttk.Combobox(frame, textvariable=freq_var, state="readonly", width=22)
        freq_combo.grid(row=2, column=1, pady=4, padx=(8, 0))

        def update_freq_values(*args) -> None:
            if cat_var.get() == self.t('television'):
                freq_combo['values'] = [str(f) for f in range(200, 501)]
                freq_var.set("200")
            else:
                freq_combo['values'] = [f"{f/10:.1f}" for f in range(880, 1081, 2)]
                freq_combo.current(0)
            update_freq_values()
            cat_var.trace('w', update_freq_values)

        ttk.Combobox(frame, textvariable=cat_var, values=[self.t('radio'), self.t('television')],
                     state="readonly", width=22).grid(row=1, column=1, pady=4, padx=(8, 0))

        def on_confirm() -> None:
            name = name_var.get().strip()
            if not name:
                return
            cat = "Radio" if cat_var.get() == self.t('radio') else "Television"
            if cat == "Television":
                freq = freq_var.get()
            else:
                freq = str(int(float(freq_var.get()) * 1000))

            tree = ET.parse(self.file_path)
            root = tree.getroot()
            channels = root.find('Channels')
            if channels is None:
                channels = ET.SubElement(root, 'Channels')

            ch_entry = ET.SubElement(channels, 'ChannelEntry', {
                'ID': str(uuid.uuid4()),
                'name': name,
                'cat': cat,
                'freq': freq,
                'startscript': 'main',
            })

            script_entry = ET.SubElement(ch_entry, 'ScriptEntry', {
                'ID': str(uuid.uuid4()),
                'name': 'main',
                'startdelay': '0',
                'timestampmode': 'Static',
                'loopmin': '1',
                'loopmax': '12',
            })
            ET.SubElement(script_entry, 'ExitOptions')

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_channel_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

        name_entry = frame.grid_slaves(row=0, column=1)[0]
        name_entry.focus_set()

    def edit_channel(self) -> None:
        ch_index = self._get_tree_index(self.channel_list)
        if ch_index is None or not self.file_path:
            return
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        channels = root.find('Channels')
        if channels is None:
            return
        ch_entries = channels.findall('ChannelEntry')
        if ch_index >= len(ch_entries):
            return
        ch_entry = ch_entries[ch_index]
        current_name = ch_entry.get('name', '')
        current_cat = ch_entry.get('cat', 'Radio')
        current_freq = ch_entry.get('freq', '88000')

        dialog = tk.Toplevel(self)
        dialog.title(self.t('edit_channel_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('channel_name_label')).grid(row=0, column=0, sticky=tk.W, pady=4)
        name_var = tk.StringVar(value=current_name)
        ttk.Entry(frame, textvariable=name_var, width=24).grid(row=0, column=1, pady=4, padx=(8, 0))

        ttk.Label(frame, text=self.t('channel_category')).grid(row=1, column=0, sticky=tk.W, pady=4)
        cat_display = self.t('radio') if current_cat == "Radio" else self.t('television')
        cat_var = tk.StringVar(value=cat_display)

        ttk.Label(frame, text=self.t('channel_frequency')).grid(row=2, column=0, sticky=tk.W, pady=4)
        if current_cat == "Television":
            freq_default = current_freq
        else:
            freq_default = f"{int(current_freq) / 1000:.1f}"
        freq_var = tk.StringVar(value=freq_default)
        freq_combo = ttk.Combobox(frame, textvariable=freq_var, state="readonly", width=22)
        freq_combo.grid(row=2, column=1, pady=4, padx=(8, 0))
        if current_cat == "Television":
            freq_combo['values'] = [str(f) for f in range(200, 501)]
        else:
            freq_combo['values'] = [f"{f/10:.1f}" for f in range(880, 1081, 2)]

        def update_freq_values(*args) -> None:
            if cat_var.get() == self.t('television'):
                freq_combo['values'] = [str(f) for f in range(200, 501)]
                freq_var.set("200")
            else:
                freq_combo['values'] = [f"{f/10:.1f}" for f in range(880, 1081, 2)]
                freq_var.set("88.0")

        cat_var.trace('w', update_freq_values)

        ttk.Combobox(frame, textvariable=cat_var, values=[self.t('radio'), self.t('television')],
                     state="readonly", width=22).grid(row=1, column=1, pady=4, padx=(8, 0))

        def on_confirm() -> None:
            name = name_var.get().strip()
            if not name:
                return
            cat = "Radio" if cat_var.get() == self.t('radio') else "Television"
            if cat == "Television":
                freq = freq_var.get()
            else:
                freq = str(int(float(freq_var.get()) * 1000))

            ch_entry.set('name', name)
            ch_entry.set('cat', cat)
            ch_entry.set('freq', freq)

            ET.indent(tree, space='  ')
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
            self.refresh_channel_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

        name_entry = frame.grid_slaves(row=0, column=1)[0]
        name_entry.focus_set()

    def _get_tree_index(self, tree: ttk.Treeview) -> int | None:
        sel = tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except (ValueError, TypeError):
            return None

    def show_page(self, name: str) -> None:
        self.page_welcome.pack_forget()
        self.page_channel.pack_forget()
        self.page_translate.pack_forget()
        self.page_server_translate.pack_forget()

        if name == 'welcome':
            self.page_welcome.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        elif name == 'channel':
            self.page_channel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        elif name == 'translate':
            self.page_translate.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self.refresh_lang_list()
        elif name == 'server_translate':
            self.page_server_translate.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self._refresh_st_lang_list()
            messagebox.showinfo(self.t('st_info_title'), self.t('st_info_text'))

    def checkOutputDir(self):
        current_dir = _base_dir()
        output_dir = os.path.join(current_dir, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建 output 文件夹：{output_dir}")
        else:
            print(f"output 文件夹已存在：{output_dir}")

    def refresh_lang_list(self) -> None:
        for item in self.lang_list.get_children():
            self.lang_list.delete(item)
        if not self.file_path:
            return
        project_dir = os.path.dirname(self.file_path)
        translate_dir = os.path.join(project_dir, 'Translate')
        if not os.path.isdir(translate_dir):
            return
        for lang in ALLOWED_LANGUAGES:
            lang_dir = os.path.join(translate_dir, lang)
            json_file = os.path.join(lang_dir, 'RadioData.json')
            if os.path.isdir(lang_dir) and os.path.isfile(json_file):
                self.lang_list.insert('', tk.END, values=(lang,))

    def add_language(self) -> None:
        if not self.file_path:
            return
        project_dir = os.path.dirname(self.file_path)
        translate_dir = os.path.join(project_dir, 'Translate')

        existing = set()
        for item in self.lang_list.get_children():
            existing.add(self.lang_list.item(item, 'values')[0])

        available = [l for l in ALLOWED_LANGUAGES if l not in existing]

        dialog = tk.Toplevel(self)
        dialog.title(self.t('add_language_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('select_language')).pack(anchor=tk.W)
        lang_var = tk.StringVar()
        lang_combo = ttk.Combobox(frame, textvariable=lang_var, values=available, state='readonly', width=20)
        lang_combo.pack(fill=tk.X, pady=(2, 8))
        if available:
            lang_combo.current(0)

        def on_confirm() -> None:
            lang = lang_var.get()
            if not lang:
                return
            lang_dir = os.path.join(translate_dir, lang)
            os.makedirs(lang_dir, exist_ok=True)
            json_path = os.path.join(lang_dir, 'RadioData.json')
            src_json = os.path.join(translate_dir, self.language, 'RadioData.json')
            try:
                with open(src_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.refresh_lang_list()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def delete_language(self) -> None:
        sel = self.lang_list.selection()
        if not sel:
            return
        lang = self.lang_list.item(sel[0], 'values')[0]
        if lang == self.language:
            return
        if not messagebox.askyesno(self.t('confirm_delete'),
                                   self.t('confirm_delete_language').replace('{lang}', lang)):
            return
        project_dir = os.path.dirname(self.file_path)
        lang_dir = os.path.join(project_dir, 'Translate', lang)
        if os.path.isdir(lang_dir):
            shutil.rmtree(lang_dir)
        self.refresh_lang_list()
        for item in self.translate_tree.get_children():
            self.translate_tree.delete(item)

    def _on_lang_right_click(self, event: tk.Event) -> None:
        item = self.lang_list.identify_row(event.y)
        if item:
            self.lang_list.selection_set(item)
            self.lang_context.tk_popup(event.x_root, event.y_root)

    def _open_lang_folder(self) -> None:
        sel = self.lang_list.selection()
        if not sel or not self.file_path:
            return
        lang = self.lang_list.item(sel[0], 'values')[0]
        project_dir = os.path.dirname(self.file_path)
        lang_dir = os.path.join(project_dir, 'Translate', lang)
        if os.path.isdir(lang_dir):
            os.startfile(lang_dir)

    def _load_translate_data(self) -> None:
        for item in self.translate_tree.get_children():
            self.translate_tree.delete(item)
        sel = self.lang_list.selection()
        if not sel or not self.file_path:
            return
        lang = self.lang_list.item(sel[0], 'values')[0]
        project_dir = os.path.dirname(self.file_path)
        json_path = os.path.join(project_dir, 'Translate', lang, 'RadioData.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        for key, val in data.items():
            search = self.translate_search_var.get().strip().lower()
            if getattr(self.translate_search_entry, '_placeholder_active', True) is False:
                search = ''
            if search and search not in key.lower() and search not in str(val).lower():
                continue
            self.translate_tree.insert('', tk.END, values=(key, val))

    def _edit_translate_entry(self, event: tk.Event | None = None) -> None:
        sel = self.translate_tree.selection()
        if not sel:
            return
        values = self.translate_tree.item(sel[0], 'values')
        if not values:
            return
        key, val = values[0], values[1]

        sel = self.lang_list.selection()
        if not sel:
            return
        lang = self.lang_list.item(sel[0], 'values')[0]

        dialog = tk.Toplevel(self)
        dialog.title(self.t('edit_translate_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('id_label')).pack(anchor=tk.W)
        id_entry = ttk.Entry(frame, width=50)
        id_entry.insert(0, key)
        id_entry.config(state='readonly')
        id_entry.pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('text_label')).pack(anchor=tk.W)
        text_var = tk.StringVar(value=val)
        ttk.Entry(frame, textvariable=text_var, width=50).pack(fill=tk.X, pady=(2, 8))

        def on_confirm() -> None:
            new_text = text_var.get().strip()
            if not new_text:
                return
            project_dir = os.path.dirname(self.file_path)
            json_path = os.path.join(project_dir, 'Translate', lang, 'RadioData.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data[key] = new_text
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._load_translate_data()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def _refresh_st_lang_list(self) -> None:
        for item in self.st_lang_list.get_children():
            self.st_lang_list.delete(item)
        if not self.file_path:
            return
        project_dir = os.path.dirname(self.file_path)
        st_dir = os.path.join(project_dir, 'ServerTranslate')
        if not os.path.isdir(st_dir):
            return
        for lang in os.listdir(st_dir):
            json_file = os.path.join(st_dir, lang, 'RadioData.json')
            if os.path.isdir(os.path.join(st_dir, lang)) and os.path.isfile(json_file):
                self.st_lang_list.insert('', tk.END, values=(lang,))

    def _load_st_translate_data(self) -> None:
        for item in self.st_translate_tree.get_children():
            self.st_translate_tree.delete(item)
        sel = self.st_lang_list.selection()
        if not sel or not self.file_path:
            return
        lang = self.st_lang_list.item(sel[0], 'values')[0]
        project_dir = os.path.dirname(self.file_path)
        json_path = os.path.join(project_dir, 'ServerTranslate', lang, 'RadioData.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        for key, val in data.items():
            search = self.st_search_var.get().strip().lower()
            if getattr(self.st_search_entry, '_placeholder_active', True) is False:
                search = ''
            if search and search not in key.lower() and search not in str(val).lower():
                continue
            self.st_translate_tree.insert('', tk.END, values=(key, val))

    def _edit_st_translate_entry(self, event: tk.Event | None = None) -> None:
        sel = self.st_translate_tree.selection()
        if not sel:
            return
        values = self.st_translate_tree.item(sel[0], 'values')
        if not values:
            return
        key, val = values[0], values[1]

        sel = self.st_lang_list.selection()
        if not sel:
            return
        lang = self.st_lang_list.item(sel[0], 'values')[0]

        dialog = tk.Toplevel(self)
        dialog.title(self.t('edit_translate_title'))
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack()

        ttk.Label(frame, text=self.t('id_label')).pack(anchor=tk.W)
        id_entry = ttk.Entry(frame, width=50)
        id_entry.insert(0, key)
        id_entry.config(state='readonly')
        id_entry.pack(fill=tk.X, pady=(2, 8))

        ttk.Label(frame, text=self.t('text_label')).pack(anchor=tk.W)
        text_var = tk.StringVar(value=val)
        ttk.Entry(frame, textvariable=text_var, width=50).pack(fill=tk.X, pady=(2, 8))

        def on_confirm() -> None:
            project_dir = os.path.dirname(self.file_path)
            json_path = os.path.join(project_dir, 'ServerTranslate', lang, 'RadioData.json')
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            data[key] = text_var.get()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._load_st_translate_data()
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text=self.t('confirm'), command=on_confirm).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text=self.t('cancel'), command=dialog.destroy).pack(side=tk.LEFT, padx=4)

        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")

    def _sync_st_language(self) -> None:
        sel = self.st_lang_list.selection()
        if not sel:
            messagebox.showwarning(self.t('warning'), self.t('no_lang_selected'))
            return
        lang = self.st_lang_list.item(sel[0], 'values')[0]
        project_dir = os.path.dirname(self.file_path)

        # Read source translations from Translate/{lang}/RadioData.json
        src_path = os.path.join(project_dir, 'Translate', lang, 'RadioData.json')
        try:
            with open(src_path, 'r', encoding='utf-8') as f:
                src_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            src_data = {}

        # Read target server translations from ServerTranslate/{lang}/RadioData.json
        dst_path = os.path.join(project_dir, 'ServerTranslate', lang, 'RadioData.json')
        try:
            with open(dst_path, 'r', encoding='utf-8') as f:
                dst_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            dst_data = {}

        # Append all source entries to server translate file
        for key, val in src_data.items():
            dst_data[key] = val

        with open(dst_path, 'w', encoding='utf-8') as f:
            json.dump(dst_data, f, ensure_ascii=False, indent=4)

        self._load_st_translate_data()
        messagebox.showinfo(self.t('notice'), self.t('sync_success'))

    def _open_st_lang_folder(self) -> None:
        sel = self.st_lang_list.selection()
        if not sel or not self.file_path:
            return
        lang = self.st_lang_list.item(sel[0], 'values')[0]
        project_dir = os.path.dirname(self.file_path)
        lang_dir = os.path.join(project_dir, 'ServerTranslate', lang)
        if os.path.isdir(lang_dir):
            os.startfile(lang_dir)

if __name__ == '__main__':
    app = App()
    app.mainloop()
    