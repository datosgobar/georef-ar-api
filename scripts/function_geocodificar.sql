CREATE OR REPLACE FUNCTION geocodificar(geom TEXT, altura INTEGER, alt_ini INTEGER, alt_fin INTEGER, OUT result JSON)
  RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
  interpolation TEXT;
  line_merge    TEXT;
  ret           VARCHAR;
  code          INTEGER;
BEGIN
  SELECT st_linemerge(geom)
  INTO line_merge;
  CASE
    WHEN (SELECT st_numgeometries(line_merge)) = 1
    THEN
      SELECT st_astext(st_line_interpolate_point(
                           st_makeline(line_merge),
                           CASE
                           WHEN ((altura - alt_ini) / (alt_fin - alt_ini) :: FLOAT) > 1
                             THEN 1
                           WHEN ((altura - alt_ini) / (alt_fin - alt_ini) :: FLOAT) < 0
                             THEN 0
                           ELSE ((altura - alt_ini) / (alt_fin - alt_ini) :: FLOAT)
                           END
                       ))
      INTO interpolation;
      SELECT st_y(interpolation) || ',' || st_x(interpolation)
      INTO ret;
      code := 1;
  ELSE
    ret := 'Líneas discontinuas';
    code := 0;
  END CASE;
  result:=json_build_object('code', code, 'result', ret);
  EXCEPTION
  WHEN OTHERS
    THEN
      result:=json_build_object('code', 2, 'result', SQLERRM);
END;
$$;