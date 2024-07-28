import wx
import pickle
import os
import re
import tempfile

class ResultViewerDialog(wx.Dialog):
    def __init__(self, parent, result):
        super().__init__(parent, title="View Result", size=(300, 150))
        panel = wx.Panel(self)
        
        self.result_text = wx.TextCtrl(panel, value=result, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.result_text.SetFocus()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.result_text, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        self.ShowModal()

class HelpDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Help", size=(400, 300))
        panel = wx.Panel(self)
        
        help_text = """
        Welcome to the Accessible Calculator!

        Available functions:
        1. Enter equations using keyboard or buttons.
        2. Use basic arithmetic operations: +, -, *, /.
        3. View results list.
        4. Edit previous equations.
        5. Copy results or full equations.
        6. Delete individual results or clear all results.

        Keyboard shortcuts:
        - F1: Open this help window.
        - Enter: Calculate result.
        - Alt+F4: Close application.
        - Applications key: Open context menu for result list options.
        - Delete: Delete selected result from the list.

        You can use the Tab key to navigate between interface elements.
        
        To access additional options for results, select a result and press the Applications key 
        (or right-click) to open the context menu. This menu includes options to edit, view, 
        copy, or delete results.
        """
        
        self.help_text = wx.TextCtrl(panel, value=help_text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.help_text, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)

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
        
        self.button_panel = wx.Panel(self.main_panel)
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '+', '=',
            'Clear', 'Help'
        ]
        
        button_sizer = wx.GridSizer(5, 4, 5, 5)
        for label in buttons:
            button = wx.Button(self.button_panel, label=label)
            button.Bind(wx.EVT_BUTTON, self.on_button_click)
            button_sizer.Add(button, 0, wx.EXPAND)
        self.button_panel.SetSizer(button_sizer)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.equation_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.result_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.button_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        self.main_panel.SetSizer(main_sizer)
        
        self.statusbar = self.CreateStatusBar()
        
        self.results = []
        self.load_results()
        self.update_result_list()
        
        self.editing_index = None
        
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.Show()
        print("AccessibleCalculator initialized and shown")

    def on_key_down(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_F1:
            self.show_help()
        else:
            event.Skip()

    def on_char(self, event):
        key_code = event.GetKeyCode()
        if chr(key_code) in '0123456789+-*/().':
            event.Skip()
        elif key_code < 32 or key_code in [wx.WXK_DELETE, wx.WXK_BACK, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_HOME, wx.WXK_END, wx.WXK_TAB]:
            event.Skip()
        
    def on_list_key_down(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_DELETE:
            self.on_delete_item(event)
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
        else:
            current_text = self.equation.GetValue()
            self.equation.SetValue(current_text + label)

    def calculate_result(self):
        print("Calculating result")
        equation = self.equation.GetValue()
        
        if not re.match(r'^[\d\+\-\*/\(\)\.\s]*$', equation):
            print("Invalid characters in equation")
            wx.MessageBox("Invalid characters in equation. Please use only numbers and operators.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        if not any(op in equation for op in ['+', '-', '*', '/']):
            print("No operation in equation")
            wx.MessageBox("Please enter a complete equation with at least one operation.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        try:
            result = eval(equation)
            print(f"Equation: {equation}, Result: {result}")
            if self.editing_index is not None:
                self.results[self.editing_index] = (equation, str(result))
                self.editing_index = None
            else:
                self.add_result(equation, result)
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
        if len(self.results) > 5:
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
        menu.Append(self.popupID1, "Edit")
        menu.Append(self.popupID2, "View Result")
        menu.Append(self.popupID3, "Copy Full")
        menu.Append(self.popupID4, "Copy Result")
        menu.Append(self.popupID5, "Delete Item")
        menu.Append(self.popupID6, "Clear All")

        self.PopupMenu(menu)
        menu.Destroy()

    def on_edit(self, event):
        index = self.result_list.GetSelection()
        if index != wx.NOT_FOUND:
            equation, _ = self.results[index]
            self.equation.SetValue(equation)
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
            with open(file_path, 'rb') as f:
                self.results = pickle.load(f)
        print(f"Loaded results: {self.results}")

    def show_help(self):
        print("Showing help dialog")
        help_dialog = HelpDialog(self)
        help_dialog.ShowModal()
        help_dialog.Destroy()

    def on_close(self, event):
        print("Closing application")
        self.Destroy()

if __name__ == '__main__':
    app = wx.App()
    frame = AccessibleCalculator()
    app.MainLoop()