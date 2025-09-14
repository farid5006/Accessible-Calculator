import wx
import pickle
import os
import re
import tempfile
import math
import threading
import keyboard
import time

class ResultViewerDialog(wx.Dialog):
    def __init__(self, parent, result):
        super().__init__(parent, title="View Result", size=(300, 150))
        panel = wx.Panel(self)
        
        self.result_text = wx.TextCtrl(panel, value=result, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.result_text.SetFocus()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.result_text, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        self.ShowModal()

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

class HelpDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Help", size=(450, 400))
        
        self.help_texts = {
            "English": """
Welcome to the Accessible Calculator!

Keyboard shortcuts:
- F1: Open this help window.
- Enter: Calculate result.
- Alt+F4: Close application.
- Ctrl+D: Focus on equation input box.
- Ctrl+Shift+V: Toggle Advanced Mode.
- Alt+Ctrl+Z: Paste from clipboard, calculate, and show the result.
- Applications key: Open context menu for result list options.

Context menu shortcuts:
- Ctrl+E: Edit selected result.
- Ctrl+V: View selected result.
- Ctrl+Shift+C: Copy full equation and result.
- Ctrl+C: Copy only the result.
- Delete: Delete selected result.
- Ctrl+L: Clear all results.

Advanced Mode:
- Press the "Advanced" button or Ctrl+Shift+V to show/hide a panel with advanced mathematical functions and constants.
- You can type functions (e.g., sin(30)) or use the buttons.
            """,
            "العربية": """
مرحباً بك في الآلة الحاسبة الميسرة!

اختصارات لوحة المفاتيح:
- F1: فتح نافذة المساعدة هذه.
- Enter: حساب النتيجة.
- Alt+F4: إغلاق التطبيق.
- Ctrl+D: التركيز على مربع إدخال المعادلة.
- Ctrl+Shift+V: تفعيل/إلغاء الوضع المتقدم.
- Alt+Ctrl+Z: لصق من الحافظة، ثم الحساب، وإظهار النتيجة.
- مفتاح التطبيقات: فتح قائمة السياق لخيارات قائمة النتائج.

اختصارات قائمة السياق:
- Ctrl+E: تعديل النتيجة المحددة.
- Ctrl+V: عرض النتيجة المحددة.
- Ctrl+Shift+C: نسخ المعادلة والنتيجة كاملة.
- Ctrl+C: نسخ النتيجة فقط.
- Delete: حذف النتيجة المحددة.
- Ctrl+L: مسح كل النتائج.

الوضع المتقدم:
- اضغط على زر "Advanced" أو Ctrl+Shift+V لإظهار/إخفاء لوحة تحتوي على دوال وثوابت رياضية متقدمة.
- يمكنك كتابة الدوال يدويًا (مثال: sin(30)) أو استخدام الأزرار.
            """
        }

        panel = wx.Panel(self)
        
        lang_label = wx.StaticText(panel, label="Language / اللغة:")
        self.lang_choice = wx.Choice(panel, choices=list(self.help_texts.keys()))
        self.help_text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)

        self.lang_choice.SetSelection(1)  # Default to Arabic
        self.help_text_ctrl.SetValue(self.help_texts["العربية"])

        self.lang_choice.Bind(wx.EVT_CHOICE, self.on_language_select)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(lang_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        top_sizer.Add(self.lang_choice, 1, wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.help_text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        panel.SetSizer(main_sizer)
        self.lang_choice.SetFocus()

    def on_language_select(self, event):
        selected_lang = self.lang_choice.GetStringSelection()
        self.help_text_ctrl.SetValue(self.help_texts[selected_lang])

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

class AccessibleCalculator(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Accessible Calculator')
        print("Initializing AccessibleCalculator")
        self.main_panel = wx.Panel(self)
        
        self.equation_panel = wx.Panel(self.main_panel)
        self.equation = wx.TextCtrl(self.equation_panel, style=wx.TE_PROCESS_ENTER)
        self.equation.SetHint("Enter equation")
        self.equation.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.equation.Bind(wx.EVT_CHAR, self.on_char)
        
        equation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        equation_sizer.Add(self.equation, 1, wx.EXPAND | wx.ALL, 5)
        self.equation_panel.SetSizer(equation_sizer)
        
        self.result_panel = wx.Panel(self.main_panel)
        self.result_label = wx.StaticText(self.result_panel, label="Results List:")
        self.result_list = wx.ListBox(self.result_panel, style=wx.LB_SINGLE)
        self.result_list.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.result_list.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        
        result_sizer = wx.BoxSizer(wx.VERTICAL)
        result_sizer.Add(self.result_label, 0, wx.BOTTOM, 5)
        result_sizer.Add(self.result_list, 1, wx.EXPAND)
        self.result_panel.SetSizer(result_sizer)

        self.advanced_button_panel = wx.Panel(self.main_panel)
        advanced_buttons = [
            'sin(', 'cos(', 'tan(', 'sqrt(', 'degrees(', 'radians(',
            'asin(', 'acos(', 'atan(', 'log(', 'log10(', 'exp(',
            'factorial(', 'pi', 'e', '(', ')', ''
        ]
        advanced_button_sizer = wx.GridSizer(3, 6, 5, 5)
        for label in advanced_buttons:
            if label:
                button = wx.Button(self.advanced_button_panel, label=label)
                button.Bind(wx.EVT_BUTTON, self.on_button_click)
                advanced_button_sizer.Add(button, 0, wx.EXPAND)
            else:
                advanced_button_sizer.AddStretchSpacer()
        self.advanced_button_panel.SetSizer(advanced_button_sizer)
        
        self.button_panel = wx.Panel(self.main_panel)
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '+', '=',
            'Clear', 'Help', '^', 'Advanced'
        ]
        
        button_sizer = wx.GridSizer(5, 4, 5, 5)
        for label in buttons:
            button = wx.Button(self.button_panel, label=label)
            button.Bind(wx.EVT_BUTTON, self.on_button_click)
            if label == 'Help':
                button.SetToolTip("Opens the help window (F1)")
            button_sizer.Add(button, 0, wx.EXPAND)
        self.button_panel.SetSizer(button_sizer)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.equation_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.result_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.advanced_button_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.button_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        self.main_panel.SetSizer(main_sizer)
        
        self.statusbar = self.CreateStatusBar()
        
        self.results = []
        self.load_results()
        self.update_result_list()
        
        self.editing_index = None
        
        self.setup_accelerators()
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.advanced_button_panel.Hide()
        self.main_panel.Layout()
        
        self.hotkey_thread = threading.Thread(target=self.listen_for_hotkeys, daemon=True)
        self.hotkey_thread.start()
        
        self.Show()
        print("AccessibleCalculator initialized and shown")

    def setup_accelerators(self):
        focus_id = wx.NewId()
        help_id = wx.NewId()
        close_id = wx.NewId()
        advanced_id = wx.NewId()

        self.Bind(wx.EVT_MENU, self.focus_equation, id=focus_id)
        self.Bind(wx.EVT_MENU, lambda event: self.show_help(), id=help_id)
        self.Bind(wx.EVT_MENU, lambda event: self.Close(), id=close_id)
        self.Bind(wx.EVT_MENU, self.toggle_advanced_mode, id=advanced_id)

        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('D'), focus_id),
            (wx.ACCEL_NORMAL, wx.WXK_F1, help_id),
            (wx.ACCEL_ALT, wx.WXK_F4, close_id),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('V'), advanced_id)
        ])
        self.SetAcceleratorTable(accel_tbl)

    def listen_for_hotkeys(self):
        """Runs in a separate thread to listen for global hotkeys."""
        print("Hotkey listener thread started.")
        try:
            keyboard.add_hotkey(
                'alt+ctrl+z',
                lambda: wx.CallAfter(self.paste_and_calculate)
            )
            keyboard.wait()
        except Exception as e:
            print(f"Error in hotkey listener thread: {e}")

    def paste_and_calculate(self):
        """Pastes from clipboard and calculates."""
        print("Paste and calculate hotkey activated.")
        
        self.Iconize(False)
        self.Show(True)
        self.Raise()
        self.RequestUserAttention()

        text_data = wx.TextDataObject()
        clipboard_opened = False
        if wx.TheClipboard.Open():
            clipboard_opened = True
            success = wx.TheClipboard.GetData(text_data)
            wx.TheClipboard.Close()
        
        if clipboard_opened and success:
            clipboard_text = text_data.GetText()
            if clipboard_text:
                self.equation.SetValue(clipboard_text)
                self.calculate_result(equation_str=clipboard_text)
            else:
                self.statusbar.SetStatusText("Clipboard is empty.", 0)
                wx.CallLater(2000, self.clear_statusbar)
        else:
            print("Could not retrieve text from clipboard.")
            self.statusbar.SetStatusText("Could not retrieve text from clipboard.", 0)
            wx.CallLater(2000, self.clear_statusbar)

    def toggle_advanced_mode(self, event=None):
        is_shown = self.advanced_button_panel.IsShown()
        self.advanced_button_panel.Show(not is_shown)
        self.main_panel.GetSizer().Layout()
        self.Fit()

    def on_char(self, event):
        event.Skip()
        
    def on_list_key_down(self, event):
        key_code = event.GetKeyCode()
        modifiers = event.GetModifiers()
        if key_code == wx.WXK_DELETE:
            self.on_delete_item(event)
        elif key_code == ord('E') and modifiers == wx.MOD_CONTROL:
            self.on_edit(event)
        elif key_code == ord('V') and modifiers == wx.MOD_CONTROL:
            self.on_view_result(event)
        elif key_code == ord('C') and modifiers == (wx.MOD_CONTROL | wx.MOD_SHIFT):
            self.on_copy_full(event)
        elif key_code == ord('C') and modifiers == wx.MOD_CONTROL:
            self.on_copy_result(event)
        elif key_code == ord('L') and modifiers == wx.MOD_CONTROL:
            self.on_clear_all(event)
        else:
            event.Skip()

    def on_enter(self, event):
        print("Enter key pressed")
        self.calculate_result()

    def on_button_click(self, event):
        label = event.GetEventObject().GetLabel()
        print(f"Button clicked: {label}")
        if label == '=':
            self.calculate_result()
        elif label == 'Clear':
            self.clear_equation()
        elif label == 'Help':
            self.show_help()
        elif label == 'Advanced':
            self.toggle_advanced_mode()
        else:
            current_text = self.equation.GetValue()
            self.equation.SetValue(current_text + label)
            self.equation.SetFocus()
            self.equation.SetInsertionPointEnd()

    def calculate_result(self, equation_str=None):
        print("Calculating result")
        equation = equation_str if equation_str is not None else self.equation.GetValue()
        
        if not re.match(r'^[a-zA-Z0-9\s\+\-\*/\(\)\.\^]*$', equation):
            print("Invalid characters in equation")
            wx.MessageBox("Invalid characters in equation. Please use only numbers, operators, and valid functions.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        has_operator = any(op in equation for op in ['+', '-', '*', '/', '^'])
        has_function = any(func in equation for func in ['sin', 'cos', 'tan', 'sqrt', 'log', 'factorial', 'degrees', 'radians', 'exp'])
        if not has_operator and not has_function and 'pi' not in equation and 'e' not in equation:
            print("No operation in equation")
            wx.MessageBox("Please enter a complete equation with at least one operation or function.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        try:
            equation_to_eval = equation.replace('^', '**')
            
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}

            result = eval(equation_to_eval, {"__builtins__": {}}, allowed_names)
            
            print(f"Equation: {equation}, Result: {result}")
            if self.editing_index is not None:
                self.results[self.editing_index] = (equation, str(result))
                self.editing_index = None
            else:
                self.add_result(equation, result)
            
            if equation_str is None:
                self.equation.Clear()

        except Exception as e:
            print(f"Error in calculation: {str(e)}")
            error_message = self.get_user_friendly_error(str(e))
            wx.MessageBox(error_message, "Error", wx.OK | wx.ICON_ERROR)
        finally:
            self.update_result_list()
            print(f"Results list after calculation: {self.results}")
            if self.results:
                self.result_list.SetSelection(0)
                self.result_list.SetFocus()

    def get_user_friendly_error(self, error_message):
        if "invalid syntax" in error_message:
            return "The equation contains invalid syntax. Please check your equation and try again."
        elif "division by zero" in error_message:
            return "Division by zero is not allowed. Please check your equation."
        elif "invalid literal for int()" in error_message:
            return "Invalid number format. Please use proper number format."
        elif "math domain error" in error_message:
            return "Mathematical error. The operation you're trying to perform is not valid."
        else:
            return "An error occurred while calculating. Please check your equation and try again."

    def add_result(self, equation, result):
        print(f"Adding result: {equation} = {result}")
        self.results.insert(0, (equation, str(result)))
        if len(self.results) > 10:
            self.results.pop()
        self.save_results()

    def update_result_list(self):
        print("Updating result list")
        self.result_list.Clear()
        for _, result in self.results:
            self.result_list.Append(result)
        print(f"Result list items: {[self.result_list.GetString(i) for i in range(self.result_list.GetCount())]}")

    def clear_equation(self):
        print("Clearing equation")
        self.equation.Clear()
        self.equation.SetFocus()

    def on_context_menu(self, event):
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()
            
            self.Bind(wx.EVT_MENU, self.on_edit, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.on_view_result, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.on_copy_full, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.on_copy_result, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.on_delete_item, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.on_clear_all, id=self.popupID6)

        menu = wx.Menu()
        menu.Append(self.popupID1, "Edit\tCtrl+E")
        menu.Append(self.popupID2, "View Result\tCtrl+V")
        menu.Append(self.popupID3, "Copy Full\tCtrl+Shift+C")
        menu.Append(self.popupID4, "Copy Result\tCtrl+C")
        menu.Append(self.popupID5, "Delete Item\tDel")
        menu.Append(self.popupID6, "Clear All\tCtrl+L")

        self.PopupMenu(menu)
        menu.Destroy()

    def on_edit(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            equation, _ = self.results[index]
            self.equation.SetValue(equation)
            self.equation.SetFocus()
            self.equation.SetInsertionPointEnd()
            self.editing_index = index

    def on_view_result(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            _, result = self.results[index]
            ResultViewerDialog(self, result)

    def on_copy_full(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            equation, result = self.results[index]
            self.copy_to_clipboard(f"{equation} = {result}")

    def on_copy_result(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            _, result = self.results[index]
            self.copy_to_clipboard(result)

    def on_delete_item(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            del self.results[index]
            self.update_result_list()
            self.save_results()

    def on_clear_all(self, event):
        self.results.clear()
        self.update_result_list()
        self.save_results()

    def copy_to_clipboard(self, text):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
            self.statusbar.SetStatusText("Copied to clipboard!", 0)
            wx.CallLater(2000, self.clear_statusbar)

    def clear_statusbar(self):
        self.statusbar.SetStatusText("", 0)

    def save_results(self):
        print("Saving results")
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, 'calculator_results.pkl')
        with open(file_path, 'wb') as f:
            pickle.dump(self.results, f)

    def load_results(self):
        print("Loading results")
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, 'calculator_results.pkl')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    self.results = pickle.load(f)
            except (pickle.UnpicklingError, EOFError):
                self.results = []
        print(f"Loaded results: {self.results}")

    def show_help(self):
        print("Showing help dialog")
        help_dialog = HelpDialog(self)
        help_dialog.ShowModal()
        help_dialog.Destroy()

    def on_close(self, event):
        print("Closing application")
        self.Destroy()

    def focus_equation(self, event):
        self.Raise()
        self.equation.SetFocus()

if __name__ == '__main__':
    app = wx.App()
    frame = AccessibleCalculator()
    app.MainLoop()