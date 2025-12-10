import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useMemo } from 'react';
import { StringParam, useQueryParam, withDefault } from 'use-query-params';
import dayjs from 'dayjs';

export const MonthYearPicker = () => {
    const [monthyear, setMonthYear] = useQueryParam('monthyear', withDefault(StringParam, new Date().getFullYear().toString()))
    const date = useMemo(() => dayjs(monthyear), [monthyear])
    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
                label={'year'}
                openTo="year"
                views={['year']}
                value={date}
                onChange={(newValue) => {
                    console.log('newValue:', newValue)
                    setMonthYear(newValue?.format('YYYY'))
                }}
            />
        </LocalizationProvider>
    );
}