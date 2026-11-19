import os
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preview_window import PreviewWindow
from print_manager import (
    MAX_COPIES,
    MIN_COPIES,
    PrintDialog,
    PrintError,
    calculate_print_layout,
    list_printers,
    print_image,
)


class PrintLayoutTests(unittest.TestCase):
    def test_portrait_photo_on_portrait_paper_no_rotation(self):
        rotate, rect = calculate_print_layout((1200, 1800), (4961, 7016), dpi=(600, 600))
        self.assertFalse(rotate)
        x0, y0, x1, y1 = rect
        self.assertEqual(y0, 0)
        self.assertEqual(y1, 7016)
        self.assertGreater(x0, 0)
        self.assertAlmostEqual((x1 - x0) / (y1 - y0), 1200 / 1800, places=3)

    def test_landscape_photo_on_portrait_paper_auto_rotates(self):
        rotate, rect = calculate_print_layout((1800, 1200), (4961, 7016), dpi=(600, 600))
        self.assertTrue(rotate)
        x0, y0, x1, y1 = rect
        self.assertEqual(y1 - y0, 7016)
        self.assertAlmostEqual((x1 - x0) / (y1 - y0), 1200 / 1800, places=3)

    def test_non_square_dpi_preserves_physical_aspect(self):
        rotate, rect = calculate_print_layout((1000, 1000), (600, 1200), dpi=(300, 600))
        self.assertFalse(rotate)
        x0, y0, x1, y1 = rect
        self.assertEqual((x0, y0, x1, y1), (0, 0, 600, 1200))

    def test_invalid_dimensions_raise(self):
        with self.assertRaises(ValueError):
            calculate_print_layout((0, 100), (1000, 1000))
        with self.assertRaises(ValueError):
            calculate_print_layout((100, 100), (0, 1000))


class PrintImageTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.img_path = os.path.join(self.tmpdir.name, "composite.jpg")
        Image.new("RGB", (800, 1200), (240, 98, 123)).save(self.img_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_file_raises_print_error(self):
        with self.assertRaises(PrintError):
            print_image(os.path.join(self.tmpdir.name, "missing.jpg"), printer_name="Test")

    def test_invalid_copies_raises_print_error(self):
        with self.assertRaises(PrintError):
            print_image(self.img_path, printer_name="Test", copies=0)
        with self.assertRaises(PrintError):
            print_image(self.img_path, printer_name="Test", copies=MAX_COPIES + 1)

    @unittest.skipUnless(sys.platform == "win32", "Windows-only GDI print test")
    def test_windows_pdf_direct_print_multiple_copies(self):
        printers = list_printers()
        if "Microsoft Print to PDF" not in printers:
            self.skipTest("Microsoft Print to PDF tidak tersedia")

        out_pdf = os.path.join(self.tmpdir.name, "printed.pdf")
        result = print_image(
            self.img_path,
            printer_name="Microsoft Print to PDF",
            copies=2,
            output_path=out_pdf,
        )
        self.assertEqual(result["printer"], "Microsoft Print to PDF")
        self.assertEqual(result["copies"], 2)
        self.assertTrue(os.path.exists(out_pdf))
        self.assertGreater(os.path.getsize(out_pdf), 1000)


class PreviewPrintUiTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.img_path = os.path.join(self.tmpdir.name, "photo.jpg")
        Image.new("RGB", (600, 900), (40, 180, 140)).save(self.img_path)
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.tmpdir.cleanup()

    def test_print_button_keeps_preview_open_and_opens_dialog(self):
        opened_dialogs = []

        def on_print(photo_path, parent_window):
            dialog = PrintDialog(parent_window, photo_path)
            opened_dialogs.append(dialog)

        preview = PreviewWindow(
            self.img_path,
            Mock(),
            Mock(),
            Mock(),
            print_callback=on_print,
        )

        with patch("print_manager.list_printers", return_value=["Printer A", "Printer B"]), \
             patch("print_manager.get_default_printer", return_value="Printer A"):
            preview.show(wait=False)
            self.root.update()

            print_buttons = [
                w for w in preview._focus_widgets
                if "Print Foto" in str(w.cget("text"))
            ]
            self.assertEqual(len(print_buttons), 1)

            # Klik tombol Print -> preview harus tetap terbuka
            print_buttons[0].invoke()
            self.root.update()

            self.assertFalse(preview._closed)
            self.assertTrue(preview.root.winfo_exists())
            self.assertEqual(len(opened_dialogs), 1)

            dialog = opened_dialogs[0]
            self.assertEqual(dialog.printer_var.get(), "Printer A")
            self.assertEqual(dialog.copies_var.get(), MIN_COPIES)

            # Uji stepper copies
            dialog._inc_copies()
            dialog._inc_copies()
            self.assertEqual(dialog.copies_var.get(), 3)
            dialog._dec_copies()
            self.assertEqual(dialog.copies_var.get(), 2)

            # Idle timeout tidak menutup PreviewWindow saat PrintDialog masih terbuka
            preview._on_idle_timeout()
            self.assertFalse(preview._closed)
            self.assertTrue(preview.root.winfo_exists())

            # Tutup PrintDialog -> PreviewWindow tetap terbuka
            dialog._handle_close()
            self.root.update()
            self.assertFalse(preview._closed)
            self.assertTrue(preview.root.winfo_exists())

            preview._close()


if __name__ == "__main__":
    unittest.main()
