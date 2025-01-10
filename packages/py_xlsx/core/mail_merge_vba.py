import os
import win32com.client as win32
import pythoncom

def mail_merge_using_vba(word_template: str, output_folder: str, label_name: str = "Internal") -> None:
    """
    Performs mail merge by calling a VBA macro that also sets sensitivity labels.
    
    Args:
        word_template: Path to the Word template document
        output_folder: Path where merged documents will be saved
        label_name: Name of the sensitivity label to apply
    """
    try:
        # Initialize COM
        pythoncom.CoInitialize()
        
        # Create a new instance of Word
        word_app = win32.DispatchEx("Word.Application")  # Use DispatchEx for new instance
        word_app.Visible = False  # Make Word invisible
        word_app.DisplayAlerts = False  # Suppress alerts
        
        try:
            # Load macro document
            data_dir = os.path.dirname(word_template)
            macro_file = os.path.join(data_dir, "mail_merge_macros.docm")
            
            if not os.path.exists(macro_file):
                raise FileNotFoundError(f"Macro file not found: {macro_file}")
                
            # Open the macro document
            macro_doc = word_app.Documents.Open(macro_file)
            
            # Get data source path
            data_source = os.path.join(data_dir, "workbook.xlsx")
            
            if not os.path.exists(data_source):
                raise FileNotFoundError(f"Data source not found: {data_source}")
            
            # Create output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)
            
            print("\n=== Starting Mail Merge using VBA ===")
            print(f"Template: {word_template}")
            print(f"Data source: {data_source}")
            print(f"Output folder: {output_folder}")
            
            # Call the VBA macro (which now handles labels)
            word_app.Run("ExecuteMailMerge", word_template, data_source, output_folder)
            
            print("\nMail merge completed successfully")
            print(f"Output saved to: {output_folder}")
            
        except Exception as e:
            print(f"\nError during mail merge: {str(e)}")
            raise
            
        finally:
            # Always try to quit this specific instance
            try:
                word_app.Quit()
                del word_app  # Release the COM object
            except:
                pass
                
    finally:
        pythoncom.CoUninitialize() 