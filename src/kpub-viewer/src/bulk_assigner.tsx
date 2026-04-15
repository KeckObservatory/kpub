import Button from '@mui/material/Button';
import { useState } from 'react';
import { useStateContext, type Article } from './App';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import RadioGroup from '@mui/material/RadioGroup';
import { apiURL } from './config';
import Radio from '@mui/material/Radio';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Stack from '@mui/material/Stack';

export interface BulkAssignerProps {
    selectedArticles: Article[];
    isOpen: boolean;
    isKOA: boolean;
    handleClose: () => void;
}

interface BulkAssignerContentProps {
    selectedArticles: Article[];
    isKOA: boolean;
    handleClose: () => void;
}

export const BulkAssignerContent = (props: BulkAssignerContentProps) => {
    const { selectedArticles, handleClose, isKOA } = props;
    const [selectedOption, setSelectedOption] = useState('Keck');
    const [notes, setNotes] = useState('');
    const context = useStateContext()

    const handleSave = async () => {
        console.log('Selected Option:', selectedOption);

        const body: any = {
            [isKOA ? 'koa_affiliation' : 'affiliation']: selectedOption,
            articles: selectedArticles,
        };

        if (notes.trim()) {
            body.notes = notes;
        }

        const resp = await fetch(`${apiURL}/update_affiliation`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })

        if (resp.ok) {
            const respBody = await resp.json()
            console.log('Updated article:', respBody)
            if (context !== null) {
                var newArticles = [...context.articles]
                respBody.updated_articles.forEach((article: Article) => {
                    const idx = context?.articles.findIndex((a) => a._id === article._id)
                    if (idx > -1) {
                        newArticles.splice(idx, 1, article)
                    }
                })
                context?.setArticles(newArticles)
            }
        }
        handleClose();
    }

    return (
        <>
            <DialogContent>
                <Stack spacing={2}>
                    <AffiliationButtonGroup
                        selectedOption={selectedOption}
                        setSelectedOption={setSelectedOption}
                        row={false}
                        isKOA={isKOA}
                    />
                    <TextField
                        label="Notes"
                        multiline
                        rows={4}
                        fullWidth
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Enter any notes about this bulk change..."
                    />
                </Stack>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} color="secondary">
                    Cancel
                </Button>
                <Button onClick={handleSave} color="primary" variant="contained">
                    Save
                </Button>
            </DialogActions>
        </>
    )
}

interface AffiliationButtonGroupProps {
    selectedOption: string;
    setSelectedOption: (option: string) => void;
    row: boolean;
    isKOA: boolean;
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
                {props.isKOA ? (
                    <>
                        <FormControlLabel value={true} control={<Radio />} label="KOA" />
                        <FormControlLabel value={false} control={<Radio />} label="Not KOA" />
                    </>
                ) : (
                    <>
                        <FormControlLabel value="Keck" control={<Radio />} label="Keck" />
                        <FormControlLabel value="unknown" control={<Radio />} label="Unknown" />
                        <FormControlLabel value="unrelated" control={<Radio />} label="Unrelated" />
                    </>
                )}
            </RadioGroup>
        </FormControl>
    )
}