import Button from '@mui/material/Button';
import { useState } from 'react';
import { useStateContext, type Article } from './App';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import RadioGroup from '@mui/material/RadioGroup';
import Radio from '@mui/material/Radio';
import FormControlLabel from '@mui/material/FormControlLabel';

export interface BulkAssignerProps {
    selectedArticles: Article[];
    isOpen: boolean;
    handleClose: () => void;
}

interface AffiliationButtonGroupProps {
    selectedOption: string;
    setSelectedOption: (option: string) => void;
    row: boolean;
}

export const AffiliationButtonGroup = (props: AffiliationButtonGroupProps) => {
    return (
        <FormControl>
            <FormLabel id="demo-radio-buttons-group-label">Affiliation</FormLabel>
            <RadioGroup
                row={props.row}
                name="affiliation-buttons-group"
                value={props.selectedOption}
                onChange={(e) => props.setSelectedOption(e.target.value)}
            >
                <FormControlLabel value="Keck" control={<Radio />} label="Keck" />
                <FormControlLabel value="unknown" control={<Radio />} label="Unknown" />
                <FormControlLabel value="unrelated" control={<Radio />} label="Unrelated" />
            </RadioGroup>
        </FormControl>
    )
}


export const BulkAssigner = (props: BulkAssignerProps) => {

    const { selectedArticles, isOpen, handleClose} = props;

    const [selectedOption, setSelectedOption] = useState('Keck');

    const context = useStateContext()

    const handleSave = async () => {
        // Perform the save operation here
        console.log('Selected Option:', selectedOption);

        const resp = await fetch(`https://vm-dev-appserver/api/kpub/update_affiliation}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                affiliation: selectedOption,
                articles: [selectedArticles],
            }),
        })

        if (resp.ok) {
            const updatedArticle = await resp.json()
            console.log('Updated article:', updatedArticle)
            context?.setArticles(context.articles.map((article) => {
                if (article._id === updatedArticle._id) {
                    return updatedArticle
                }
                return article
            }))
        }
        handleClose();
    }

    return (
        <Dialog open={isOpen} onClose={handleClose}>
            <DialogTitle>Bulk Edit Selected Articles</DialogTitle>
            <DialogContent>
                <AffiliationButtonGroup
                    selectedOption={selectedOption}
                    setSelectedOption={setSelectedOption}
                    row={false}
                />
                {/* <Select
                    value={selectedOption}
                    onChange={(e) => setSelectedOption(e.target.value)}
                    fullWidth
                >
                    <MenuItem value="Keck">Keck</MenuItem>
                    <MenuItem value="unknown">Unknown</MenuItem>
                    <MenuItem value="unrelated">Unrelated</MenuItem>
                </Select> */}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} color="secondary">
                    Cancel
                </Button>
                <Button onClick={handleSave} color="primary" variant="contained">
                    Save
                </Button>
            </DialogActions>
        </Dialog>
    )
}

