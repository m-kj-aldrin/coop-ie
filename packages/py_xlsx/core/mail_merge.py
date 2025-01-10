import os
import win32com.client as win32
import pythoncom

# Word constants
WD_MERGE_SUBTYPE_ACCESS = 1  # wdMergeSubTypeAccess constant value
WD_FORM_LETTERS = 0  # wdFormLetters constant value
WD_FORMAT_AUTO = 0  # wdOpenFormatAuto
WD_NORMAL_VIEW = 3  # wdNormalView

class WordEventHandler:
    def OnEvent(self, *args):
        return False  # Cancel any dialogs

def mail_merge_prelinked(word_template: str, output_folder: str) -> None:
    """Performs mail merge with a pre-linked data source."""
    word_app = None
    try:
        # Initialize COM
        pythoncom.CoInitialize()
        
        # Initialize Word with events
        word_app = win32.DispatchWithEvents("Word.Application", WordEventHandler)
        word_app.Visible = True
        word_app.DisplayAlerts = False
        
        try:
            # Validate paths
            if not os.path.exists(word_template):
                raise FileNotFoundError(f"Template file not found: {word_template}")
            
            data_dir = os.path.dirname(word_template)
            data_source = os.path.join(data_dir, "workbook.xlsx")
            
            if not os.path.exists(data_source):
                raise FileNotFoundError(f"Data source not found: {data_source}")
            
            os.makedirs(output_folder, exist_ok=True)
            
            # Get absolute paths
            word_template = os.path.abspath(word_template)
            data_source = os.path.abspath(data_source)
            output_folder = os.path.abspath(output_folder)
            
            print("\n=== Starting Mail Merge ===")
            print(f"Template: {word_template}")
            print(f"Data source: {data_source}")
            
            # Open document
            print("\nOpening document...")
            word_doc = word_app.Documents.Open(word_template)
            print("Document opened successfully")
            
            # Set up mail merge
            print("\nSetting up mail merge...")
            merge = word_doc.MailMerge
            merge.MainDocumentType = WD_FORM_LETTERS
            
            # Connect data source
            print("Connecting data source...")
            try:
                connection_string = (
                    f"Provider=Microsoft.ACE.OLEDB.12.0;"
                    f"Data Source={data_source};"
                    "Extended Properties='Excel 12.0 Xml;HDR=YES;IMEX=1';"
                    f"DefaultDir={os.path.dirname(data_source)};"
                )

                merge.OpenDataSource(
                    Name=data_source,
                    ConfirmConversions=False,
                    ReadOnly=False,
                    Format=WD_FORMAT_AUTO,
                    Connection=connection_string,
                    SQLStatement="SELECT * FROM [Incident$]",
                    SubType=WD_MERGE_SUBTYPE_ACCESS
                )
                print("Data source connected successfully")
                
                # Get field info for filenames
                print("\nAvailable fields in data source:")
                ds = merge.DataSource
                try:
                    data_fields = ds.DataFields
                    for i in range(1, data_fields.Count + 1):
                        field = data_fields.Item(i)
                        print(f"  - Field {i}: {field.Name} = {field.Value}")
                except Exception as e:
                    print(f"Error listing fields: {str(e)}")
                
                # Save each document
                print(f"\nSaving merged documents...")
                
                # Save one record at a time
                for i in range(1, ds.RecordCount + 1):
                    try:
                        # Set current record
                        ds.ActiveRecord = i
                        
                        # Get filename
                        file_name = ds.DataFields("cas").Value
                        file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_'))
                        print(f"\nProcessing record {i}:")
                        print(f"  File name: {file_name}")
                        
                        # Execute merge for this record only
                        merge.DataSource.FirstRecord = i
                        merge.DataSource.LastRecord = i
                        merge.Execute(False)
                        
                        # Save the result
                        output_file = os.path.join(output_folder, f"{file_name}.docx")
                        word_app.ActiveDocument.SaveAs2(output_file)
                        word_app.ActiveDocument.Close(SaveChanges=False)
                        print(f"  Saved as: {output_file}")
                        
                    except Exception as e:
                        print(f"Error processing record {i}: {str(e)}")
            
            except Exception as e:
                print(f"Error during merge: {str(e)}")
                raise
            
        finally:
            print("\nCleaning up...")
            try:
                # Close all open documents first
                for doc in word_app.Documents:
                    doc.Close(SaveChanges=False)
                
                # Then close Word
                word_app.Quit()
                
                # Release COM objects
                del word_doc
                del word_app
                
            except Exception as e:
                print(f"Error during cleanup: {str(e)}")
    
    finally:
        # Final COM cleanup
        try:
            pythoncom.CoUninitialize()
        except:
            pass
