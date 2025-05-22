import FormControl from "@mui/material/FormControl"
import FormControlLabel from "@mui/material/FormControlLabel"
import FormLabel from "@mui/material/FormLabel"
import InputLabel from "@mui/material/InputLabel"
import Radio from "@mui/material/Radio"
import RadioGroup from "@mui/material/RadioGroup"
import type { SelectChangeEvent } from "@mui/material/Select"
import Select from "@mui/material/Select"
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers"
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs"
import dayjs from "dayjs"
import { useState } from "react"
import { INSTRUMENTS } from "../config"
import OutlinedInput from "@mui/material/OutlinedInput"
import MenuItem from "@mui/material/MenuItem"
import Checkbox from "@mui/material/Checkbox"
import { PlotDisplay } from "./plot_display"
import Button from "@mui/material/Button"
import Dialog from "@mui/material/Dialog"
import DialogTitle from "@mui/material/DialogTitle"
import DialogContent from "@mui/material/DialogContent"
import DialogActions from "@mui/material/DialogActions"

export type CountType = 'first_author' | 'author' | 'paper'
export type PlotNames = 'data_by_count' | 'data_by_instrument' | 'data_by_year'

interface PlotTypeButtonGroupProps {
    countType: CountType
    setCountType: (option: CountType) => void
}

interface InstrumentsMultipleSelectProps {
    instruments: string[] | string
    setInstruments: (name: string[]) => void
}

const CountTypeButtonGroup = (props: PlotTypeButtonGroupProps) => {
    return (
        <FormControl>
            <FormLabel id="demo-radio-buttons-group-label">Affiliation</FormLabel>
            <RadioGroup
                row={true}
                name="plot-type-buttons-group"
                value={props.countType}
                onChange={(e) => props.setCountType(e.target.value as CountType)}
            >
                <FormControlLabel value="author" control={<Radio />} label="Author" />
                <FormControlLabel value="first_author" control={<Radio />} label="First Author" />
                <FormControlLabel value="paper" control={<Radio />} label="Paper" />
            </RadioGroup>
        </FormControl>
    )
}


const InstrumentsMultipleSelect = (props: InstrumentsMultipleSelectProps) => {
    const { instruments, setInstruments } = props

    const handleChange = (event: SelectChangeEvent<typeof instruments>) => {
        const {
            target: { value },
        } = event;
        setInstruments(
            // On autofill we get a stringified value.
            typeof value === 'string' ? value.split(',') : value,
        );
    };

    return (
        <FormControl sx={{ m: 1, width: 300 }}>
            <InputLabel id="multiple-instrument-label">Instruments</InputLabel>
            <Select
                labelId="multiple-instrument-label"
                id="multiple-instrument"
                multiple
                value={instruments}
                onChange={handleChange}
                input={<OutlinedInput label="Name" />}
            >
                {INSTRUMENTS.map((name) => (
                    <MenuItem
                        key={name}
                        value={name}
                    >
                        {name}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
}


const PlotControl = () => {
    const [countType, setCountType] = useState<CountType>("author")
    const [startYear, setStartYear] = useState<number | undefined>(2009)
    const [instruments, setInstruments] = useState<string[] | string>([])
    const [extrapolate, setExtrapolate] = useState(false)
    const [plotName, setPlotName] = useState<PlotNames>("data_by_instrument")

    return (
        <>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DatePicker
                    label={'year'}
                    openTo="year"
                    views={['year']}
                    maxDate={dayjs(new Date())}
                    minDate={dayjs('2000-01-01')}
                    value={dayjs(`${startYear}-01-01`)}
                    onChange={(newValue) => {
                        console.log('newValue:', newValue)
                        setStartYear(newValue?.year())
                    }}
                />
            </LocalizationProvider>
            {plotName === 'data_by_year' && (
                <FormControlLabel
                    control={<Checkbox checked={extrapolate} onChange={(e) => setExtrapolate(e.target.checked)} />}
                    label="Extrapolate"
                />
            )}
            {plotName === 'data_by_instrument' && (
                <InstrumentsMultipleSelect
                    instruments={instruments}
                    setInstruments={setInstruments}
                />
            )}
            {plotName === 'data_by_count' && (
                <CountTypeButtonGroup countType={countType} setCountType={setCountType} />
            )}
            <Select
                value={plotName}
                onChange={(e) => setPlotName(e.target.value as PlotNames)}
                input={<OutlinedInput label="Plot Type" />}
                label="Plot Type"
                fullWidth
            >
                <MenuItem value="data_by_count">Cumulative</MenuItem>
                <MenuItem value="data_by_instrument">By Instrument</MenuItem>
                <MenuItem value="data_by_year">By Year</MenuItem>
            </Select>
            <PlotDisplay
                plotname={plotName}
                start_year={startYear}
                instruments={typeof instruments === 'string' ? [instruments as string] : instruments}
                extrapolate={extrapolate}
                countType={countType}
            />
        </>
    )

}

export const PlotControlDialog = () => {
    const [isOpen, setIsOpen] = useState(false)

    const handleOpen = () => {
        setIsOpen(true)
    }
    const handleClose = () => {
        setIsOpen(false);
    };
    return (
        <>
            <Button color="primary" onClick={handleOpen} variant="contained">
                See Plots of published articles
            </Button>
            <Dialog maxWidth={'xl'} fullWidth open={isOpen} onClose={handleClose}>
                <DialogTitle>Plots</DialogTitle>
                <DialogContent>
                    <PlotControl />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose} color="secondary">
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    )
}