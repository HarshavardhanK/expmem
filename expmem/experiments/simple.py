from expmem.agents.coder import GenerateCode, CodeGenerator
from expmem.agents.coder import CodeGeneratorSimple, GenerateCodeSimple
from expmem.agents.debugger import CodeExecutorAgent

from expmem.datasets.DatasetFactory import DatasetFactory

from expmem.experiments.utils import setup_csv, append_result, extract_python_code

def test_direct():


    dataset = DatasetFactory('MBPP').get_dataset()
    #q1 = dataset[0].prompt

    code_gen = CodeGenerator()
    #res = code_gen(q1)
    #print(res)

    #code_gen.model.inspect_history(n=1)

    # code = extract_python_code(res.code)
    # print(code)

    code_exec = CodeExecutorAgent()
    # res = code_exec(prompt=q1, code=code, sample_io=dataset[0].sample_io)
    # print('----------- Execution Analysis -------------: ', res['prediction'].analysis)
    # print(res)

    result = []
    file = "mbpp_results_detail2.csv"
    setup_csv(file)

    for data in dataset:

        code_sol = code_gen(data.prompt)
        code = extract_python_code(code_sol.code)

        exec_res = code_exec(
            prompt=data.prompt,
            sample_ios=data.sample_io,
            code=code,
            tests=data.test,
            entry_point=data.entry_point
        )

        _ = append_result(filename=file, 
                          summary=code_sol.summary, 
                          detailed=code_sol.detailed, 
                          data=data, ID=dataset._id, 
                          code=code, 
                          exec_res=exec_res)
        
        result.append(exec_res)
    
        # Print progress
        if exec_res['result']:
            print(f'Test cases passed for ID: {data[dataset._id]}')
        #print(exec_res)


    #Count number of test cases passed
    #result is Bool value
    passed = [1 for r in result if r['result']]
    total_passed = sum(passed)
    print(f'Total test cases passed: {total_passed}')


def serial_main():

    dataset = DatasetFactory('HumanEval').get_dataset()

    code_gen = CodeGeneratorSimple()

    code_exec = CodeExecutorAgent()
    
    result = []
    file = "humanEval_simple3.csv"
    
    setup_csv(file)

    for data in dataset:

        code_sol = code_gen(data.prompt)
        code = extract_python_code(code_sol.code)

        exec_res = code_exec(
            prompt=data.prompt,
            sample_ios=data.sample_io,
            code=code,
            tests=data.test,
            entry_point=data.entry_point
        )

        _ = append_result(filename=file, 
                          data=data, 
                          code=code, 
                          ID=dataset._id,
                          summary=None,
                          detailed=None,
                          exec_res=exec_res)
        
        result.append(exec_res)
    
        # Print progress
        if exec_res['result']:
            print(f'Test cases passed for task_id: {data[dataset._id]}')
        #print(exec_res)


    #Count number of test cases passed
    #result is Bool value
    passed = [1 for r in result if r['result']]
    total_passed = sum(passed)
    print(f'Total test cases passed: {total_passed}')


if __name__ == '__main__':
    #test_direct()
    serial_main()