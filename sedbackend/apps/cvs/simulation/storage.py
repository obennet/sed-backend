import re
import sys
from math import isnan

from mysql.connector.pooling import PooledMySQLConnection
import pandas as pd
from mysql.connector import Error

from fastapi.logger import logger

from desim import interface as des
from desim.data import NonTechCost, TimeFormat
from desim.simulation import Process
from plusminus import BaseArithmeticParser

from typing import List
from sedbackend.apps.cvs.design.storage import get_all_designs

from mysqlsb import FetchType, MySQLStatementBuilder

from sedbackend.apps.cvs.life_cycle.storage import get_dsm_from_file_id
from sedbackend.apps.cvs.simulation.models import SimulationResult
from sedbackend.apps.cvs.vcs.storage import get_vcss
from sedbackend.libs.formula_parser import expressions as expr
from sedbackend.apps.cvs.simulation import models
import sedbackend.apps.cvs.simulation.exceptions as e
from sedbackend.apps.cvs.vcs import storage as vcs_storage
from sedbackend.apps.cvs.life_cycle import storage as life_cycle_storage
from sedbackend.apps.core.files import exceptions as file_exceptions

SIM_SETTINGS_TABLE = "cvs_simulation_settings"
SIM_SETTINGS_COLUMNS = ['project', 'time_unit', 'flow_process', 'flow_start_time', 'flow_time',
                        'interarrival_time', 'start_time', 'end_time', 'discount_rate', 'non_tech_add', 'monte_carlo',
                        'runs']

TIME_FORMAT_DICT = dict({
    'year': TimeFormat.YEAR,
    'month': TimeFormat.MONTH,
    'week': TimeFormat.WEEK,
    'day': TimeFormat.DAY,
    'hour': TimeFormat.HOUR,
    'minutes': TimeFormat.MINUTES
})


def run_simulation(db_connection: PooledMySQLConnection, sim_settings: models.EditSimSettings,
                   project_id: int, vcs_ids: List[int],
                   design_group_ids: List[int], user_id, normalized_npv: bool = False,
                   is_multiprocessing: bool = False,
                   ) -> SimulationResult:
    if not check_sim_settings(sim_settings):
        raise e.BadlyFormattedSettingsException

    interarrival = sim_settings.interarrival_time
    flow_time = sim_settings.flow_time
    runtime = sim_settings.end_time - sim_settings.start_time
    non_tech_add = sim_settings.non_tech_add
    discount_rate = sim_settings.discount_rate
    process = sim_settings.flow_process
    time_unit = TIME_FORMAT_DICT.get(sim_settings.time_unit)
    is_monte_carlo = sim_settings.monte_carlo
    runs = sim_settings.runs

    all_sim_data = get_all_sim_data(db_connection, vcs_ids, design_group_ids)

    all_market_values = get_all_market_values(db_connection, vcs_ids)

    all_designs = get_all_designs(db_connection, design_group_ids)

    all_vd_design_values = get_all_vd_design_values(db_connection, [design.id for design in all_designs])

    unique_vds = {}
    for vd in all_vd_design_values:
        element_id = vd["id"]
        if element_id not in unique_vds:
            unique_vds[element_id] = {"id": vd["id"], "name": vd["name"], "unit": vd["unit"], "project_id": vd["project"]}
    all_vds = list(unique_vds.values())

    all_dsm_ids = life_cycle_storage.get_multiple_dsm_file_id(db_connection, vcs_ids)

    all_vcss = get_vcss(db_connection, project_id, vcs_ids, user_id)

    sim_result = SimulationResult(designs=all_designs, vcss=all_vcss, vds=all_vds, runs=[])

    for vcs_id in vcs_ids:
        market_values = [mi for mi in all_market_values if mi['vcs'] == vcs_id]
        dsm_id = [dsm for dsm in all_dsm_ids if dsm[0] == vcs_id]
        dsm = None
        if len(dsm_id) > 0:
            try:
                dsm = get_dsm_from_file_id(db_connection, dsm_id[0][1], user_id)
                dsm = fill_dsm_with_zeros(dsm)
            except file_exceptions.FileNotFoundException:
                pass
        for design_group_id in design_group_ids:
            sim_data = [sd for sd in all_sim_data if sd['vcs'] == vcs_id and sd['design_group'] == design_group_id]
            if sim_data is None or sim_data == []:
                raise e.VcsFailedException

            if not check_entity_rate(sim_data, process):
                raise e.RateWrongOrderException

            designs = [design.id for design in all_designs if design.design_group_id == design_group_id]

            if designs is None or []:
                raise e.DesignIdsNotFoundException

            for design in designs:
                vd_values = [vd for vd in all_vd_design_values if vd['design'] == design]
                processes, non_tech_processes = populate_processes(non_tech_add, sim_data, design, market_values,
                                                                   vd_values)

                if dsm is None:
                    dsm = create_simple_dsm(processes)

                sim = des.Des()

                try:
                    if is_monte_carlo and not is_multiprocessing:
                        results = sim.run_monte_carlo_simulation(flow_time, interarrival, process, processes,
                                                                 non_tech_processes,
                                                                 non_tech_add, dsm, time_unit, discount_rate, runtime,
                                                                 runs)
                    elif is_monte_carlo and is_multiprocessing:
                        results = sim.run_parallell_simulations(flow_time, interarrival, process, processes,
                                                                non_tech_processes,
                                                                non_tech_add, dsm, time_unit, discount_rate, runtime,
                                                                runs)
                    else:
                        results = sim.run_simulation(flow_time, interarrival, process, processes, non_tech_processes,
                                                     non_tech_add, dsm, time_unit,
                                                     discount_rate, runtime)

                except Exception as exc:
                    tb = sys.exc_info()[2]
                    logger.debug(
                        f'{exc.__class__}, {exc}, {exc.with_traceback(tb)}')
                    print(f'{exc.__class__}, {exc}')
                    raise e.SimulationFailedException

                sim_run_res = models.Simulation(
                    time=results.timesteps[-1],
                    mean_NPV=results.normalize_npv() if normalized_npv else results.mean_npv(),
                    max_NPVs=results.all_max_npv(),
                    mean_payback_time=results.mean_npv_payback_time(),
                    all_npvs=results.npvs,
                    payback_time=results.mean_npv_payback_time(),
                    surplus_value_end_result=results.npvs[0][-1],
                    design_id=design,
                    vcs_id=vcs_id,
                )

                sim_result.runs.append(sim_run_res)
    logger.debug('Returning the results')
    return sim_result


def populate_processes(non_tech_add: NonTechCost, db_results, design: int,
                       mi_values=None,
                       vd_values=None):
    if mi_values is None:
        mi_values = []
    parser = BaseArithmeticParser()

    technical_processes = []
    non_tech_processes = []

    for row in db_results:
        vd_values_row = [vd for vd in vd_values if vd['vcs_row'] == row['id'] and vd['design'] == design]
        if row['category'] != 'Technical processes':
            try:
                non_tech = models.NonTechnicalProcess(
                    cost=parser.evaluate(parse_formula(row['cost'], vd_values_row, mi_values, row)),
                    revenue=parser.evaluate(
                        parse_formula(row['revenue'], vd_values_row, mi_values, row)),
                    name=row['iso_name'])
            except Exception as exc:
                logger.debug(f'{exc.__class__}, {exc}')
                raise e.FormulaEvalException(row['id'])
            non_tech_processes.append(non_tech)

        elif row['iso_name'] is not None and row['sub_name'] is None:
            try:
                time = parser.evaluate(parse_formula(
                    row['time'], vd_values, mi_values, row))
                cost_formula = parse_formula(row['cost'], vd_values, mi_values, row)
                revenue_formula = parse_formula(
                    row['revenue'], vd_values, mi_values, row)
                p = Process(row['id'],
                            time,
                            parser.evaluate(expr.replace_all(
                                'time', time, cost_formula)),
                            parser.evaluate(expr.replace_all(
                                'time', time, revenue_formula)),
                            row['iso_name'], non_tech_add, TIME_FORMAT_DICT.get(
                        row['time_unit'].lower())
                            )
                if p.time < 0:
                    raise e.NegativeTimeException(row['id'])
            except Exception as exc:
                logger.debug(f'{exc.__class__}, {exc}')
                raise e.FormulaEvalException(row['id'])
            technical_processes.append(p)
        elif row['sub_name'] is not None:
            sub_name = f'{row["sub_name"]} ({row["iso_name"]})'
            try:
                time = parser.evaluate(parse_formula(
                    row['time'], vd_values, mi_values, row))
                cost_formula = parse_formula(row['cost'], vd_values, mi_values, row)
                revenue_formula = parse_formula(
                    row['revenue'], vd_values, mi_values, row)
                p = Process(row['id'],
                            time,
                            parser.evaluate(expr.replace_all(
                                'time', time, cost_formula)),
                            parser.evaluate(expr.replace_all(
                                'time', time, revenue_formula)),
                            sub_name, non_tech_add, TIME_FORMAT_DICT.get(
                        row['time_unit'].lower())
                            )

                if p.time < 0:
                    raise e.NegativeTimeException(row['id'])
            except Exception as exc:
                logger.debug(f'{exc.__class__}, {exc}')
                raise e.FormulaEvalException(row['id'])
            technical_processes.append(p)
        else:
            raise e.ProcessNotFoundException

    return technical_processes, non_tech_processes


def get_sim_data(db_connection: PooledMySQLConnection, vcs_id: int, design_group_id: int):
    query = f'SELECT cvs_vcs_rows.id, cvs_vcs_rows.iso_process, cvs_iso_processes.name as iso_name, category, \
            subprocess, cvs_subprocesses.name as sub_name, time, time_unit, cost, revenue, rate FROM cvs_vcs_rows \
            LEFT OUTER JOIN cvs_subprocesses ON cvs_vcs_rows.subprocess = cvs_subprocesses.id \
            LEFT OUTER JOIN cvs_iso_processes ON cvs_vcs_rows.iso_process = cvs_iso_processes.id \
                OR cvs_subprocesses.iso_process = cvs_iso_processes.id \
            LEFT OUTER JOIN cvs_design_mi_formulas ON cvs_vcs_rows.id = cvs_design_mi_formulas.vcs_row \
            WHERE cvs_vcs_rows.vcs = %s AND cvs_design_mi_formulas.design_group = %s ORDER BY `index`'
    with db_connection.cursor(prepared=True) as cursor:
        cursor.execute(query, [vcs_id, design_group_id])
        res = cursor.fetchall()
        res = [dict(zip(cursor.column_names, row)) for row in res]
    return res


def get_all_sim_data(db_connection: PooledMySQLConnection, vcs_ids: List[int], design_group_ids: List[int]):
    try:
        query = f'SELECT cvs_vcs_rows.id, cvs_vcs_rows.vcs, cvs_design_mi_formulas.design_group, \
                    cvs_vcs_rows.iso_process, cvs_iso_processes.name as iso_name, category, \
                    subprocess, cvs_subprocesses.name as sub_name, time, time_unit, cost, revenue, rate FROM cvs_vcs_rows \
                    LEFT OUTER JOIN cvs_subprocesses ON cvs_vcs_rows.subprocess = cvs_subprocesses.id \
                    LEFT OUTER JOIN cvs_iso_processes ON cvs_vcs_rows.iso_process = cvs_iso_processes.id \
                        OR cvs_subprocesses.iso_process = cvs_iso_processes.id \
                    LEFT OUTER JOIN cvs_design_mi_formulas ON cvs_vcs_rows.id = cvs_design_mi_formulas.vcs_row \
                    WHERE cvs_vcs_rows.vcs IN ({",".join(["%s" for _ in range(len(vcs_ids))])}) \
                    AND cvs_design_mi_formulas.design_group \
                    IN ({",".join(["%s" for _ in range(len(design_group_ids))])}) ORDER BY `index`'
        with db_connection.cursor(prepared=True) as cursor:
            cursor.execute(query, vcs_ids + design_group_ids)
            res = cursor.fetchall()
            res = [dict(zip(cursor.column_names, row)) for row in res]
    except Error as error:
        logger.debug(f'Error msg: {error.msg}')
        raise e.CouldNotFetchSimulationDataException
    return res


def get_all_vd_design_values(db_connection: PooledMySQLConnection, designs: List[int]):
    try:
        query = f'SELECT design, value, vcs_row, cvd.name, cvd.unit, cvd.id, cvd.project \
                FROM cvs_vd_design_values cvdv \
                INNER JOIN cvs_value_drivers cvd ON cvdv.value_driver = cvd.id \
                INNER JOIN cvs_vcs_need_drivers cvnd ON cvnd.value_driver = cvd.id \
                INNER JOIN cvs_stakeholder_needs csn ON csn.id = cvnd.stakeholder_need \
                WHERE design IN ({",".join(["%s" for _ in range(len(designs))])})'
        with db_connection.cursor(prepared=True) as cursor:
            cursor.execute(query, designs)
            res = cursor.fetchall()
            res = [dict(zip(cursor.column_names, row)) for row in res]
    except Error as error:
        logger.debug(f'Error msg: {error.msg}')
        raise e.CouldNotFetchValueDriverDesignValuesException
    return res


def get_simulation_settings(db_connection: PooledMySQLConnection, project_id: int):
    logger.debug(f'Fetching simulation settings for project {project_id}')

    select_statement = MySQLStatementBuilder(db_connection)
    res = select_statement.select(SIM_SETTINGS_TABLE, SIM_SETTINGS_COLUMNS) \
        .where('project = %s', [project_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if res is None:
        raise e.SimSettingsNotFoundException

    return populate_sim_settings(res)


def edit_simulation_settings(db_connection: PooledMySQLConnection, project_id: int,
                             sim_settings: models.EditSimSettings, user_id: int):
    logger.debug(f'Editing simulation settings for project {project_id}')

    if (sim_settings.flow_process is None and sim_settings.flow_start_time is None) \
            or (sim_settings.flow_process is not None and sim_settings.flow_start_time is not None):
        raise e.InvalidFlowSettingsException

    count_sim = MySQLStatementBuilder(db_connection)
    count = count_sim.count(SIM_SETTINGS_TABLE) \
        .where('project = %s', [project_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    count = count['count']

    if sim_settings.flow_process is not None:
        flow_process_exists = False
        vcss = vcs_storage.get_all_vcs(db_connection, project_id, user_id).chunk
        for vcs in vcss:
            rows = vcs_storage.get_vcs_table(db_connection, project_id, vcs.id)
            for row in rows:
                if (row.iso_process is not None and row.iso_process.name == sim_settings.flow_process) or \
                        (row.subprocess is not None and f'{row.subprocess.name} ({row.subprocess.parent_process.name})'
                         == sim_settings.flow_process):
                    flow_process_exists = True
                    break

        if not flow_process_exists:
            raise e.FlowProcessNotFoundException

    if (count == 1):
        columns = SIM_SETTINGS_COLUMNS[1:]
        set_statement = ','.join([col + ' = %s' for col in columns])

        values = [sim_settings.time_unit.value, sim_settings.flow_process, sim_settings.flow_start_time,
                  sim_settings.flow_time,
                  sim_settings.interarrival_time, sim_settings.start_time, sim_settings.end_time,
                  sim_settings.discount_rate, sim_settings.non_tech_add.value, sim_settings.monte_carlo,
                  sim_settings.runs]
        update_statement = MySQLStatementBuilder(db_connection)
        _, rows = update_statement \
            .update(table=SIM_SETTINGS_TABLE, set_statement=set_statement, values=values) \
            .where('project = %s', [project_id]) \
            .execute(return_affected_rows=True)

    elif (count == 0):
        create_sim_settings(db_connection, project_id, sim_settings)

    return True


def create_sim_settings(db_connection: PooledMySQLConnection, project_id: int,
                        sim_settings: models.EditSimSettings) -> bool:
    values = [project_id] + [sim_settings.time_unit.value, sim_settings.flow_process, sim_settings.flow_start_time,
                             sim_settings.flow_time,
                             sim_settings.interarrival_time, sim_settings.start_time, sim_settings.end_time,
                             sim_settings.discount_rate, sim_settings.non_tech_add.value, sim_settings.monte_carlo,
                             sim_settings.runs]

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement.insert(SIM_SETTINGS_TABLE, SIM_SETTINGS_COLUMNS) \
        .set_values(values) \
        .execute(fetch_type=FetchType.FETCH_NONE)

    return True


def get_all_market_values(db_connection: PooledMySQLConnection, vcs_ids: List[int]):
    try:
        query = f'SELECT * FROM cvs_market_input_values \
                WHERE cvs_market_input_values.vcs IN ({",".join(["%s" for _ in range(len(vcs_ids))])})'
        with db_connection.cursor(prepared=True) as cursor:
            cursor.execute(query, vcs_ids)
            res = cursor.fetchall()
            res = [dict(zip(cursor.column_names, row)) for row in res]
    except Error as error:
        logger.debug(f'Error msg: {error.msg}')
        raise e.CouldNotFetchMarketInputValuesException
    return res


def add_multiplication_signs(formula: str) -> str:
    # Define a regular expression pattern to find the positions where the multiplication sign is missing
    pattern = r'(\d)([a-zA-Z({\[<])|([}\])>]|})([a-zA-Z({\[<])|([}\])>]|{)(\d)'

    # Use the re.sub() function to replace the matches with the correct format
    def replace(match):
        if match.group(2):
            return f"{match.group(1)}*{match.group(2)}"
        elif match.group(3) and match.group(4):
            return f"{match.group(3)}*{match.group(4)}"

    result = re.sub(pattern, replace, formula)
    return result


def parse_if_statement(formula: str) -> str:
    # The pattern is if(condition, true_value, false_value)
    pattern = r'if\(([^,]+),([^,]+),([^,]+)\)'
    match = re.search(pattern, formula)
    parser = BaseArithmeticParser()

    if match:
        condition, true_value, false_value = match.groups()
        condition = condition.replace('=', '==')
        if parser.evaluate(condition):
            value = true_value
        else:
            value = false_value

        formula = re.sub(pattern, value.strip(), formula).strip()

    return formula


def parse_formula(formula: str, vd_values, ef_values, formula_row: dict = None) -> str:
    pattern = r'\{(?P<tag>vd|ef|process):(?P<value>[a-zA-Z0-9_]+),"([^"]+)"\}'

    formula = add_multiplication_signs(formula)

    def replace(match):
        tag, value, _ = match.groups()
        if tag == "vd":
            id_number = int(value)
            for vd in vd_values:
                if vd["id"] == id_number:
                    return str(vd["value"])
        elif tag == "ef":
            for ef in ef_values:
                id_number = int(value)
                if ef["market_input"] == id_number:
                    return str(ef["value"])
        elif formula_row and tag == "process":
            return f'({formula_row[value.lower()]})'

        return match.group()

    replaced_text = re.sub(pattern, replace, formula)
    replaced_text = re.sub(pattern, replace, replaced_text)

    replaced_text = parse_if_statement(replaced_text)

    replaced_text = re.sub(pattern, '0', replaced_text)  # If there are any tags left, replace them with 0

    return replaced_text


def check_entity_rate(db_results, flow_process_name: str):
    rate_check = True
    # Set the flow_process_index to be highest possible.
    flow_process_index = len(db_results)
    for i in range(len(db_results)):
        if db_results[i]['sub_name'] == flow_process_name or db_results[i]['iso_name'] == flow_process_name:
            flow_process_index = i

        if i > flow_process_index:
            for j in range(i, len(db_results)):
                if db_results[j]['rate'] == 'per_project' and db_results[j]['category'] == 'Technical processes':
                    print("Rate check false")
                    rate_check = False
                    break
            break

    return rate_check


def check_sim_settings(settings: models.EditSimSettings) -> bool:
    settings_check = True

    if settings.end_time - settings.start_time <= 0:
        settings_check = False

    if settings.flow_time > settings.end_time - settings.start_time:
        settings_check = False

    if settings.flow_start_time is not None and settings.flow_process is not None:
        settings_check = False

    if settings.flow_start_time is None and settings.flow_process is None:
        settings_check = False

    return settings_check


# Create DSM that only goes from one process to the other following the order of the index in the VCS
def create_simple_dsm(processes: List[Process]) -> dict:
    n = len(processes) + 2  # +2 for start and end
    dsm = dict()
    for i in range(n):
        if i == 0:
            name = "Start"
        elif i == n - 1:
            name = "End"
        else:
            name = processes[i - 1].name

        dsm.update({name: [1 if i + 1 == j else "X" if i == j else 0 for j in range(n)]})
    return dsm


def get_dsm_from_excel(path):
    pf = pd.read_excel(path)

    dsm = dict()
    for v in pf.values:
        dsm.update({v[0]: v[1::].tolist()})
    return dsm


def fill_dsm_with_zeros(dsm: dict) -> dict:
    for value in dsm.values():
        for i in range(len(value)):
            if value[i] == "" or (isinstance(value[i], float) and isnan(value[i])):
                value[i] = 0
    return dsm


def populate_sim_settings(db_result) -> models.SimSettings:
    logger.debug(f'Populating simulation settings')
    return models.SimSettings(
        project=db_result['project'],
        time_unit=db_result['time_unit'],
        flow_process=db_result['flow_process'],
        flow_start_time=db_result['flow_start_time'],
        flow_time=db_result['flow_time'],
        interarrival_time=db_result['interarrival_time'],
        start_time=db_result['start_time'],
        end_time=db_result['end_time'],
        discount_rate=db_result['discount_rate'],
        non_tech_add=db_result['non_tech_add'],
        monte_carlo=db_result['monte_carlo'],
        runs=db_result['runs']
    )
