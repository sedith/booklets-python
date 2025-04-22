import numpy as np
from pypdf import PdfReader, PdfWriter, PageObject, Transformation, PaperSize
import argparse


if __name__ == '__main__':
    ## parameters
    parser = argparse.ArgumentParser('python3 bootklets.py', description='Reorganize an A4 pdf as booklets.')
    parser.add_argument(dest='input_file', type=str, help='input file name')
    parser.add_argument(dest='booklet_size', type=int, help='number of pages per booklet (must be divisible by 4)')
    parser.add_argument('-o', dest='output_file', default='', type=str, help='ouput file name')
    parser.add_argument('-f', dest='output_format', default='A4', type=str, choices=['A3', 'A4'], help='outfile file format')
    parser.add_argument('-b', dest='add_blank', default=0, type=int, help='number of blank pages to add before the document')
    parser.add_argument('-l', dest='rectoverso_long', action='store_true', help='recto-verso on long side instead of short side')
    args = parser.parse_args()

    assert (args.booklet_size/4) % 1 == 0, 'booklet size should be divisible by 4'
    if not args.input_file.endswith('.pdf'):
        args.input_file += '.pdf'
    if not args.output_file:
        args.output_file = f'{args.input_file.split(".")[0]}_output.pdf'

    size_in = PaperSize.A4
    size_out = PaperSize.A4 if args.output_format == 'A4' else PaperSize.A3
    rescale = 1 / np.sqrt(2) if args.output_format == 'A4' else 1

    ## read input pdf
    pdf_in = PdfReader(args.input_file)
    pages_idx = np.array(range(len(pdf_in.pages)))

    ## add blank pages
    for i in range(args.add_blank):
        pages_idx = np.insert(pages_idx, 0, -1)
        pages_idx = np.append(pages_idx, -1)

    ## fill last booklet
    while len(pages_idx) % args.booklet_size != 0:
        pages_idx = np.append(pages_idx, -1)

    ## reorder pages
    pages = np.array(pages_idx).reshape((-1,int(args.booklet_size/2),2))
    pages[:,:,1] = np.flip(pages[:,:,1],1)
    pages[:,int(args.booklet_size/4):,:] = np.flip(pages[:,int(args.booklet_size/4):,:],1)
    pages = pages.reshape((-1,int(args.booklet_size/4),4), order='F')
    pages = pages[:,:,[2,0,3,1]]
    new_pages_idx = pages.reshape(-1)

    ## reordered pdf
    writer = PdfWriter()
    idx = 0
    while idx < len(new_pages_idx):
        new_page = PageObject.create_blank_page(None, size_out.width, size_out.height)

        idx_l = int(new_pages_idx[idx])  # cast to int since numpy.int64 is not accepted
        idx_r = int(new_pages_idx[idx+1])

        if idx_l > -1:
            new_page.merge_transformed_page(
                pdf_in.pages[idx_l],
                Transformation().rotate(90).translate(size_in.height, 0).scale(rescale)
            )
        if idx_r > -1:
            new_page.merge_transformed_page(
                pdf_in.pages[idx_r],
                Transformation().rotate(90).translate(size_in.height, size_in.width).scale(rescale)
            )

        if args.rectoverso_long and idx % 4:
            new_page.add_transformation(Transformation().rotate(180).translate(size_out.width, size_out.height))

        writer.add_page(new_page)
        idx += 2

    ## write to file
    with open(args.output_file, 'wb') as pdf_out:
        writer.write(pdf_out)
    writer.close()
