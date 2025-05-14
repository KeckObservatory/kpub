import { DataGrid, type GridColDef, type GridRowSelectionModel, type GridToolbarProps, type ToolbarPropsOverrides } from '@mui/x-data-grid';
import { useStateContext, type Article } from './App';
import { rows, columns, adminColumns } from './config'
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import { Toolbar } from '@mui/x-data-grid';
import { useMemo, useState } from 'react';
import { ArticleStepper } from './article_stepper';
import { BulkAssigner } from './bulk_assigner';
import { MonthYearPicker } from './monthyear_picker';


interface EditToolbarProps extends GridToolbarProps, ToolbarPropsOverrides {
    selectedArticles: Article[];
}

export function EditToolbar(props: EditToolbarProps) {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isStepperOpen, setIsStepperOpen] = useState(false);
    const context = useStateContext()

    const openDialog = (type: string) => {
        if (type === 'bulk') {
            handleOpenDialog()
        } else if (type === 'stepper') {
            handleOpenStepper()
        }
    }

    const handleOpenDialog = () => {
        setIsDialogOpen(true);
        setIsStepperOpen(false);
    };

    const handleCloseDialog = () => {
        setIsDialogOpen(false);
    };

    const handleOpenStepper = () => {
        setIsStepperOpen(true);
        setIsDialogOpen(false);
    };

    const handleCloseStepper = () => {
        setIsStepperOpen(false);
    };

    return (
        <Toolbar style={{padding: '5px', marginTop: '20px', marginBottom: '20px' }}> 
            <Stack sx={{marginBottom: '20px'}}direction="row" spacing={5}>
                <MonthYearPicker />
                {context?.isAdmin.current && (
                    <>
                        <Button color="primary" onClick={() => openDialog('bulk')} variant="contained">
                            Change Affiliation of Selected Articles
                        </Button>
                        <Button color="primary" onClick={() => openDialog('stepper')} variant="contained">
                            Bulk Change Affiliation of Selected Articles
                        </Button>
                        <ArticleStepper
                            selectedArticles={props.selectedArticles}
                            isOpen={isDialogOpen}
                            handleClose={handleCloseDialog}
                        />
                        <BulkAssigner
                            selectedArticles={props.selectedArticles}
                            isOpen={isStepperOpen}
                            handleClose={handleCloseStepper}
                        />
                    </>
                )}
            </Stack>
        </Toolbar>
    );
}

export const ArticleTable = () => {
    const [rowSelectionModel, setRowSelectionModel] = useState<GridRowSelectionModel>();
    const selectedArticles = useMemo(() => {
        // Get the selected rows based on the rowSelectionModel
        const sa = (rows as unknown as Article[]).filter((row) =>
            rowSelectionModel?.ids.has(row._id)
        );

        // Perform an action with the selected rows (e.g., log them)
        console.log('Selected Articles:', sa);
        return sa;
    }, [rowSelectionModel]);
    const context = useStateContext()

    const cols = context?.isAdmin.current ? adminColumns : columns as GridColDef<Article>[]

    return (
        <DataGrid
            getRowId={(row) => row._id}
            getRowHeight={() => 'auto'}
            slots={{
                //@ts-ignore
                toolbar: EditToolbar // Custom toolbar component
            }
            }
            slotProps={{
                toolbar: {
                    selectedArticles: selectedArticles
                } as EditToolbarProps,
            }}
            showToolbar
            onRowSelectionModelChange={(newRowSelectionModel) => {
                console.log('newRowSelectionModel', newRowSelectionModel);
                setRowSelectionModel(newRowSelectionModel);
            }}
            rowSelectionModel={rowSelectionModel}
            checkboxSelection={true}
            disableMultipleRowSelection={false}
            rows={rows as any as Article[]}
            columns={cols}
        />
    );
};