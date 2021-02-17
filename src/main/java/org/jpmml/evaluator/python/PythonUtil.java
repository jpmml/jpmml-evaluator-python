/*
 * Copyright (c) 2021 Villu Ruusmann
 *
 * This file is part of JPMML-Evaluator
 *
 * JPMML-Evaluator is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * JPMML-Evaluator is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with JPMML-Evaluator.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.jpmml.evaluator.python;

import java.io.IOException;
import java.util.Map;

import net.razorvine.pickle.Pickler;
import net.razorvine.pickle.Unpickler;
import org.dmg.pmml.FieldName;
import org.jpmml.evaluator.Evaluator;
import org.jpmml.evaluator.EvaluatorUtil;

public class PythonUtil {

	private PythonUtil(){
	}

	static
	public byte[] evaluate(Evaluator evaluator, byte[] dictBytes) throws IOException {
		Map<String, ?> arguments = (Map)unpickle(dictBytes);

		Map<String, ?> results = evaluate(evaluator, arguments);

		return pickle(results);
	}

	static
	public Map<String, ?> evaluate(Evaluator evaluator, Map<String, ?> arguments){
		Map<FieldName, ?> pmmlArguments = EvaluatorUtil.encodeKeys(arguments);

		Map<FieldName, ?> pmmlResults = evaluator.evaluate(pmmlArguments);

		return EvaluatorUtil.decodeAll(pmmlResults);
	}

	static
	private Object unpickle(byte[] bytes) throws IOException {
		Unpickler unpickler = new Unpickler();

		return unpickler.loads(bytes);
	}

	static
	private byte[] pickle(Object object) throws IOException {
		Pickler pickler = new Pickler();

		return pickler.dumps(object);
	}
}